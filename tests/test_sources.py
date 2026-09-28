from pathlib import Path

from morning_radio.sources import collect_from_directory


def test_collect_from_directory(tmp_path: Path):
    (tmp_path / "world.txt").write_text("world", encoding="utf-8")
    (tmp_path / "morning.txt").write_text("morning", encoding="utf-8")
    docs = collect_from_directory(tmp_path)
    status = {doc.source: doc.status for doc in docs}
    assert status == {"world": "ok", "morning": "ok", "ptis": "failed"}
