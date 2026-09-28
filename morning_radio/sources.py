from __future__ import annotations

import email
import imaplib
import io
import re
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from email.header import decode_header, make_header
from email.message import Message
from email.utils import parsedate_to_datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import requests
from bs4 import BeautifulSoup
from pypdf import PdfReader

from .config import Settings
from .models import SourceDocument

KST = ZoneInfo("Asia/Seoul")
_DRIVE_FILE_RE = re.compile(r"https://drive\.google\.com/file/d/([A-Za-z0-9_-]+)")
_URL_RE = re.compile(r"https?://[^\s<>\"]+")


class SourceError(RuntimeError):
    pass


@dataclass(frozen=True)
class GmailHit:
    subject: str
    received_at: datetime
    message: Message


def _decode_header(value: str | None) -> str:
    return str(make_header(decode_header(value or "")))


def _message_text(msg: Message) -> str:
    plain: list[str] = []
    html: list[str] = []
    for part in msg.walk():
        if part.get_content_maintype() == "multipart":
            continue
        disposition = (part.get("Content-Disposition") or "").lower()
        if "attachment" in disposition:
            continue
        ctype = part.get_content_type()
        payload = part.get_payload(decode=True)
        if payload is None:
            continue
        charset = part.get_content_charset() or "utf-8"
        text = payload.decode(charset, errors="replace")
        if ctype == "text/plain":
            plain.append(text)
        elif ctype == "text/html":
            html.append(BeautifulSoup(text, "html.parser").get_text("\n"))
    return "\n".join(plain or html).strip()


def _pdf_attachment_text(msg: Message) -> str | None:
    for part in msg.walk():
        filename = _decode_header(part.get_filename())
        ctype = part.get_content_type()
        if ctype == "application/pdf" or filename.lower().endswith(".pdf"):
            payload = part.get_payload(decode=True)
            if payload:
                return extract_pdf_text(payload)
    return None


def extract_pdf_text(data: bytes) -> str:
    reader = PdfReader(io.BytesIO(data))
    pages = [(page.extract_text() or "").strip() for page in reader.pages]
    text = "\n\n".join(page for page in pages if page)
    if not text.strip():
        raise SourceError("PDF에서 텍스트를 추출하지 못했습니다.")
    return text


def _google_drive_download(url: str) -> bytes:
    match = _DRIVE_FILE_RE.search(url)
    if not match:
        raise SourceError(f"Google Drive 파일 ID를 찾지 못했습니다: {url}")
    file_id = match.group(1)
    download_url = "https://drive.usercontent.google.com/download"
    response = requests.get(
        download_url,
        params={"id": file_id, "export": "download", "confirm": "t"},
        timeout=45,
    )
    response.raise_for_status()
    content_type = response.headers.get("content-type", "")
    if "text/html" in content_type.lower() and not response.content.startswith(b"%PDF"):
        raise SourceError("Drive PDF 직접 다운로드가 HTML 응답을 반환했습니다.")
    return response.content


def _message_datetime(msg: Message) -> datetime:
    value = msg.get("Date")
    if not value:
        return datetime.now(tz=timezone.utc)
    parsed = parsedate_to_datetime(value)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(KST)


def _latest_subject_message(
    client: imaplib.IMAP4_SSL,
    subject_fragment: str,
    max_age_hours: int,
) -> GmailHit:
    status, data = client.search(None, "ALL")
    if status != "OK":
        raise SourceError("Gmail IMAP 검색에 실패했습니다.")

    message_ids = (data[0] or b"").split()[-120:]
    cutoff = datetime.now(KST) - timedelta(hours=max_age_hours)
    candidates: list[GmailHit] = []

    for message_id in reversed(message_ids):
        status, raw = client.fetch(message_id, "(RFC822)")
        if status != "OK" or not raw or not isinstance(raw[0], tuple):
            continue
        msg = email.message_from_bytes(raw[0][1])
        subject = _decode_header(msg.get("Subject"))
        if subject_fragment.lower() not in subject.lower():
            continue
        received_at = _message_datetime(msg)
        if received_at < cutoff:
            continue
        candidates.append(GmailHit(subject=subject, received_at=received_at, message=msg))
        break

    if not candidates:
        raise SourceError(
            f"최근 {max_age_hours}시간 내 Gmail에서 제목 '{subject_fragment}' 메일을 찾지 못했습니다."
        )
    return candidates[0]


def _extract_report_text(hit: GmailHit) -> str:
    attachment_text = _pdf_attachment_text(hit.message)
    if attachment_text:
        return attachment_text

    body = _message_text(hit.message)
    for url in _URL_RE.findall(body):
        if "drive.google.com/file/d/" in url:
            return extract_pdf_text(_google_drive_download(url))
    if body.strip():
        return body
    raise SourceError(f"'{hit.subject}'에서 사용할 본문/PDF를 찾지 못했습니다.")


def collect_from_gmail(settings: Settings) -> list[SourceDocument]:
    if not settings.gmail_user or not settings.gmail_app_password:
        raise SourceError("GMAIL_USER / GMAIL_APP_PASSWORD가 필요합니다.")

    client = imaplib.IMAP4_SSL("imap.gmail.com", 993)
    try:
        client.login(settings.gmail_user, settings.gmail_app_password)
        client.select("INBOX", readonly=True)

        specs = [
            ("world", settings.world_subject, "WORLD BRIEFING"),
            ("morning", settings.morning_subject, "MORNING BRIEFING"),
            ("ptis", settings.ptis_subject, "PTIS"),
        ]
        docs: list[SourceDocument] = []
        for source, subject, title in specs:
            try:
                hit = _latest_subject_message(client, subject, settings.source_max_age_hours)
                text = _extract_report_text(hit)
                docs.append(
                    SourceDocument(
                        source=source,
                        title=title,
                        captured_at=hit.received_at,
                        status="ok",
                        text=text,
                        origin=f"gmail:{hit.subject}",
                    )
                )
            except Exception as exc:
                docs.append(
                    SourceDocument(
                        source=source,
                        title=title,
                        captured_at=datetime.now(KST),
                        status="failed",
                        text=f"Source unavailable: {exc}",
                        origin="gmail",
                    )
                )
        return docs
    finally:
        try:
            client.logout()
        except Exception:
            pass


def collect_from_directory(directory: Path) -> list[SourceDocument]:
    now = datetime.now(KST)
    specs = [
        ("world", "WORLD BRIEFING", "world.txt"),
        ("morning", "MORNING BRIEFING", "morning.txt"),
        ("ptis", "PTIS", "ptis.txt"),
    ]
    docs: list[SourceDocument] = []
    for source, title, filename in specs:
        path = directory / filename
        if path.exists():
            docs.append(
                SourceDocument(
                    source=source,
                    title=title,
                    captured_at=now,
                    text=path.read_text(encoding="utf-8"),
                    origin=str(path),
                )
            )
        else:
            docs.append(
                SourceDocument(
                    source=source,
                    title=title,
                    captured_at=now,
                    status="failed",
                    text=f"Missing fixture: {path}",
                    origin=str(path),
                )
            )
    return docs
