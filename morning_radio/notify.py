from __future__ import annotations

import argparse
from pathlib import Path

from dotenv import load_dotenv

from .config import Settings
from .kakao import send_ready_message
from .models import EpisodePlan


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--plan", type=Path, default=Path("output/episode-plan.json"))
    parser.add_argument("--url", default="")
    args = parser.parse_args()
    load_dotenv()
    settings = Settings.from_env()
    plan = EpisodePlan.model_validate_json(args.plan.read_text(encoding="utf-8"))
    rotated = send_ready_message(settings, plan, args.url or None)
    if rotated:
        print("WARNING: Kakao returned a rotated refresh token. Update KAKAO_REFRESH_TOKEN secret before the old token expires.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
