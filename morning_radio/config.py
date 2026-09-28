from __future__ import annotations

import os
from dataclasses import dataclass


def _int_env(name: str, default: int) -> int:
    raw = os.getenv(name)
    if not raw:
        return default
    return int(raw)


@dataclass(frozen=True)
class Settings:
    gemini_api_key: str
    gmail_user: str
    gmail_app_password: str
    world_subject: str
    morning_subject: str
    ptis_subject: str
    source_max_age_hours: int
    director_model: str
    tts_model: str
    voice_a: str
    voice_b: str
    target_minutes: int
    kakao_rest_api_key: str
    kakao_client_secret: str
    kakao_refresh_token: str
    player_base_url: str

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            gemini_api_key=os.getenv("GEMINI_API_KEY", "").strip(),
            gmail_user=os.getenv("GMAIL_USER", "").strip(),
            gmail_app_password=os.getenv("GMAIL_APP_PASSWORD", "").strip(),
            world_subject=os.getenv("WORLD_SUBJECT", "WORLD BRIEFING").strip(),
            morning_subject=os.getenv("MORNING_SUBJECT", "모닝 브리핑").strip(),
            ptis_subject=os.getenv("PTIS_SUBJECT", "[PTIS]").strip(),
            source_max_age_hours=_int_env("SOURCE_MAX_AGE_HOURS", 36),
            director_model=os.getenv("DIRECTOR_MODEL", "gemini-3.8-flash").strip(),
            tts_model=os.getenv("TTS_MODEL", "gemini-3.8-flash-tts").strip(),
            voice_a=os.getenv("VOICE_A", "Puck").strip(),
            voice_b=os.getenv("VOICE_B", "Kore").strip(),
            target_minutes=_int_env("TARGET_MINUTES", 18),
            kakao_rest_api_key=os.getenv("KAKAO_REST_API_KEY", "").strip(),
            kakao_client_secret=os.getenv("KAKAO_CLIENT_SECRET", "").strip(),
            kakao_refresh_token=os.getenv("KAKAO_REFRESH_TOKEN", "").strip(),
            player_base_url=os.getenv(
                "PLAYER_BASE_URL",
                "https://kijm32-ops.github.io/morning-radio/",
            ).strip(),
        )
