from datetime import datetime, timezone
from pathlib import Path

import morning_radio.player as player
from morning_radio.models import EpisodePlan, PodcastSegment, PodcastTurn, SourceDocument


def test_build_player_site(tmp_path: Path, monkeypatch):
    monkeypatch.setattr(player, "duration_seconds", lambda _: 618.0)
    mp3 = tmp_path / "episode.mp3"
    mp3.write_bytes(b"fake")
    turn_a = PodcastTurn(speaker="A", kind="fact", text="사실")
    turn_b = PodcastTurn(speaker="B", kind="analysis", text="해석")
    plan = EpisodePlan(
        date="2026-09-29",
        title="오늘의 테스트",
        teaser="테스트입니다.",
        target_minutes=18,
        segments=[
            PodcastSegment(title="하나", turns=[turn_a, turn_b]),
            PodcastSegment(title="둘", turns=[turn_a, turn_b]),
            PodcastSegment(title="셋", turns=[turn_a, turn_b]),
        ],
        watchpoints=["원달러"],
    )
    sources = [
        SourceDocument(
            source="world", title="WORLD", captured_at=datetime.now(timezone.utc), text="x"
        )
    ]
    out = player.build_player_site(plan, sources, mp3, tmp_path / "public")
    content = out.read_text(encoding="utf-8")
    assert "오늘의 테스트" in content
    assert "audio/today.mp3" in content
    assert (tmp_path / "public" / "episode.json").exists()
