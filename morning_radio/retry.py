from __future__ import annotations

import re
import sys
import time
from collections.abc import Callable
from typing import TypeVar

T = TypeVar("T")

_TRANSIENT_STATUS = {408, 429, 500, 502, 503, 504}
_TRANSIENT_MARKERS = (
    "service_unavailable",
    "high demand",
    "overloaded",
    "resource_exhausted",
    "deadline exceeded",
    "rate limit",
)
_STATUS_IN_MESSAGE = re.compile(r"error code:\s*(\d{3})", re.IGNORECASE)


def is_transient(exc: BaseException) -> bool:
    """일시적인 서버/쿼터 오류인지 판단한다. 인증·요청 오류(4xx)는 재시도하지 않는다."""
    status = getattr(exc, "status_code", None)
    if isinstance(status, int):
        return status in _TRANSIENT_STATUS
    text = str(exc).lower()
    match = _STATUS_IN_MESSAGE.search(text)
    if match:
        return int(match.group(1)) in _TRANSIENT_STATUS
    return any(marker in text for marker in _TRANSIENT_MARKERS)


def call_with_retry(
    fn: Callable[[], T],
    *,
    label: str,
    attempts: int = 5,
    base_delay: float = 10.0,
    sleep: Callable[[float], None] = time.sleep,
) -> T:
    for attempt in range(1, attempts + 1):
        try:
            return fn()
        except Exception as exc:
            if attempt == attempts or not is_transient(exc):
                raise
            delay = base_delay * 2 ** (attempt - 1)
            print(
                f"[retry] {label}: {type(exc).__name__} (attempt {attempt}/{attempts}); "
                f"retrying in {delay:.0f}s",
                file=sys.stderr,
            )
            sleep(delay)
    raise AssertionError("unreachable")
