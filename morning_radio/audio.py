from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path


class AudioToolError(RuntimeError):
    pass


def _require(binary: str) -> None:
    if shutil.which(binary) is None:
        raise AudioToolError(f"'{binary}' 실행 파일이 필요합니다.")


def combine_to_mp3(segment_paths: list[Path], output_path: Path) -> Path:
    if not segment_paths:
        raise AudioToolError("병합할 오디오 segment가 없습니다.")
    _require("ffmpeg")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    list_file = output_path.parent / "segments.ffconcat"
    lines = ["ffconcat version 1.0"]
    for path in segment_paths:
        escaped = str(path.resolve()).replace("'", "'\\''")
        lines.append(f"file '{escaped}'")
    list_file.write_text("\n".join(lines) + "\n", encoding="utf-8")

    command = [
        "ffmpeg",
        "-hide_banner",
        "-loglevel",
        "error",
        "-y",
        "-f",
        "concat",
        "-safe",
        "0",
        "-i",
        str(list_file),
        "-c:a",
        "libmp3lame",
        "-b:a",
        "96k",
        str(output_path),
    ]
    subprocess.run(command, check=True)
    return output_path


def duration_seconds(path: Path) -> float | None:
    if shutil.which("ffprobe") is None:
        return None
    result = subprocess.run(
        [
            "ffprobe",
            "-v",
            "quiet",
            "-print_format",
            "json",
            "-show_format",
            str(path),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    data = json.loads(result.stdout)
    try:
        return float(data["format"]["duration"])
    except (KeyError, TypeError, ValueError):
        return None
