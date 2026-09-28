from __future__ import annotations

import base64
from pathlib import Path

from google import genai

from .config import Settings
from .models import EpisodePlan, PodcastSegment


class TTSError(RuntimeError):
    pass


def _turn_content(segment: PodcastSegment) -> list[dict]:
    content: list[dict] = []
    for turn in segment.turns:
        speaker = "HostA" if turn.speaker == "A" else "HostB"
        content.append(
            {
                "type": "text",
                "text": turn.text,
                "annotations": [
                    {
                        "type": "speech_metadata",
                        "speaker": speaker,
                        "style": turn.style or "natural conversational Korean",
                    }
                ],
            }
        )
    return content


def synthesize_segments(
    settings: Settings,
    plan: EpisodePlan,
    output_dir: Path,
) -> list[Path]:
    if not settings.gemini_api_key:
        raise TTSError("GEMINI_API_KEY가 필요합니다.")
    output_dir.mkdir(parents=True, exist_ok=True)
    client = genai.Client(api_key=settings.gemini_api_key)
    paths: list[Path] = []

    for index, segment in enumerate(plan.segments, start=1):
        interaction = client.interactions.create(
            model=settings.tts_model,
            input=[{"type": "user_input", "content": _turn_content(segment)}],
            response_format={"type": "audio"},
            generation_config={
                "speech_config": {
                    "mode": "conversational",
                    "speakers": [
                        {"speaker": "HostA", "voice": settings.voice_a},
                        {"speaker": "HostB", "voice": settings.voice_b},
                    ],
                }
            },
        )
        audio = getattr(interaction, "output_audio", None)
        data = getattr(audio, "data", None) if audio else None
        if not data:
            raise TTSError(f"TTS segment {index}가 오디오 데이터를 반환하지 않았습니다.")
        path = output_dir / f"segment-{index:02d}.wav"
        path.write_bytes(base64.b64decode(data))
        paths.append(path)
    return paths
