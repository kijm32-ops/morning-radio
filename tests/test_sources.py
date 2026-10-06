from datetime import datetime, timedelta
from email.message import EmailMessage
from email.utils import format_datetime
from pathlib import Path

import pytest

from morning_radio.sources import (
    KST,
    SourceError,
    _all_mail_folder,
    _latest_subject_message,
    _recent_headers,
    collect_from_directory,
)


def test_collect_from_directory(tmp_path: Path):
    (tmp_path / "world.txt").write_text("world", encoding="utf-8")
    (tmp_path / "morning.txt").write_text("morning", encoding="utf-8")
    docs = collect_from_directory(tmp_path)
    status = {doc.source: doc.status for doc in docs}
    assert status == {"world": "ok", "morning": "ok", "ptis": "failed"}


def _message(subject: str, age_hours: float, body: str = "body") -> bytes:
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["Date"] = format_datetime(datetime.now(KST) - timedelta(hours=age_hours))
    msg.set_content(body)
    return msg.as_bytes()


class FakeImap:
    def __init__(self, messages: list[bytes], folders: list[bytes] | None = None):
        self.messages = messages
        self.folders = folders or []

    def list(self):
        return "OK", self.folders

    def search(self, charset, criterion):
        return "OK", [b" ".join(str(i + 1).encode() for i in range(len(self.messages)))]

    def fetch(self, message_set, parts):
        if isinstance(message_set, bytes):
            message_set = message_set.decode()
        first, _, last = message_set.partition(":")
        last = last or first
        out = []
        for number in range(int(first), int(last) + 1):
            raw = self.messages[number - 1]
            if "HEADER.FIELDS" in parts:
                head = raw.split(b"\n\n", 1)[0] + b"\n\n"
                out.append((f"{number} (BODY[HEADER.FIELDS]".encode(), head))
            else:
                out.append((f"{number} (BODY[]".encode(), raw))
            out.append(b")")
        return "OK", out


def test_all_mail_folder_uses_special_use_flag_not_name():
    client = FakeImap(
        [],
        folders=[
            b'(\\HasNoChildren) "/" "INBOX"',
            b'(\\HasNoChildren \\All) "/" "[Gmail]/&vPSwuNzVzNQ-"',
        ],
    )
    assert _all_mail_folder(client) == '"[Gmail]/&vPSwuNzVzNQ-"'


def test_all_mail_folder_missing_returns_none():
    assert _all_mail_folder(FakeImap([], folders=[b'(\\HasNoChildren) "/" "INBOX"'])) is None


def test_latest_message_skips_error_notices_and_old_mail():
    client = FakeImap(
        [
            _message("WORLD BRIEFING | 2026년 10월 4일", age_hours=60),
            _message("WORLD BRIEFING | 2026년 10월 5일", age_hours=20, body="real"),
            _message("WORLD BRIEFING 오류 | 2026년 10월 6일", age_hours=2),
        ]
    )
    headers = _recent_headers(client)
    hit = _latest_subject_message(client, headers, "WORLD BRIEFING", 36)
    assert hit.subject == "WORLD BRIEFING | 2026년 10월 5일"
    assert "real" in hit.message.get_payload(decode=True).decode()


def test_latest_message_raises_when_all_candidates_too_old():
    client = FakeImap([_message("[PTIS] 오늘의 특가 리포트", age_hours=100)])
    headers = _recent_headers(client)
    with pytest.raises(SourceError):
        _latest_subject_message(client, headers, "[PTIS]", 36)
