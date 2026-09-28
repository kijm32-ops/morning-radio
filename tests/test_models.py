from datetime import datetime, timezone

from morning_radio.models import EpisodePlan, PodcastSegment, PodcastTurn, SourceDocument


def test_episode_all_turns():
    turn_a = PodcastTurn(speaker="A", kind="fact", text="첫 번째 사실입니다.")
    turn_b = PodcastTurn(speaker="B", kind="counterpoint", text="다른 설명도 가능합니다.")
    plan = EpisodePlan(
        date="2026-09-29",
        title="테스트",
        teaser="테스트 티저",
        target_minutes=18,
        segments=[
            PodcastSegment(title="1", turns=[turn_a, turn_b]),
            PodcastSegment(title="2", turns=[turn_a, turn_b]),
            PodcastSegment(title="3", turns=[turn_a, turn_b]),
        ],
    )
    assert len(plan.all_turns) == 6


def test_source_document():
    doc = SourceDocument(
        source="world",
        title="WORLD",
        captured_at=datetime.now(timezone.utc),
        text="hello",
    )
    assert doc.status == "ok"
