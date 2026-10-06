from __future__ import annotations

import argparse
import json
from pathlib import Path

from dotenv import load_dotenv

from .audio import combine_to_mp3, duration_seconds
from .config import Settings
from .director import build_episode_plan
from .player import build_player_site
from .sources import collect_from_directory, collect_from_gmail
from .tts import synthesize_segments


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a MORNING RADIO episode")
    parser.add_argument("--source-mode", choices=["gmail", "directory"], default="gmail")
    parser.add_argument("--source-dir", type=Path, default=Path("data/inbox"))
    parser.add_argument("--work-dir", type=Path, default=Path("output"))
    parser.add_argument("--public-dir", type=Path, default=Path("public"))
    parser.add_argument("--plan-only", action="store_true")
    return parser.parse_args()


def main() -> int:
    load_dotenv()
    args = parse_args()
    settings = Settings.from_env()

    sources = (
        collect_from_gmail(settings)
        if args.source_mode == "gmail"
        else collect_from_directory(args.source_dir)
    )
    for item in sources:
        print(f"[source] {item.source}: {item.status}" + (f" - {item.text}" if item.status == "failed" else ""))
    ok_sources = [item for item in sources if item.status != "failed"]
    if not ok_sources:
        raise RuntimeError("WORLD/MORNING/PTIS 소스가 모두 실패했습니다.")

    args.work_dir.mkdir(parents=True, exist_ok=True)
    plan = build_episode_plan(settings, sources)
    plan_path = args.work_dir / "episode-plan.json"
    plan_path.write_text(plan.model_dump_json(indent=2), encoding="utf-8")

    if args.plan_only:
        print(plan_path)
        return 0

    segment_paths = synthesize_segments(settings, plan, args.work_dir / "segments")
    mp3_path = combine_to_mp3(segment_paths, args.work_dir / "morning-radio.mp3")
    build_player_site(plan, sources, mp3_path, args.public_dir)

    manifest = {
        "title": plan.title,
        "date": plan.date,
        "duration_seconds": duration_seconds(mp3_path),
        "sources": {item.source: item.status for item in sources},
        "mp3": str(mp3_path),
        "public": str(args.public_dir),
    }
    (args.work_dir / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(manifest, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
