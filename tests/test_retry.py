import pytest

from morning_radio.retry import call_with_retry, is_transient


class _StatusError(Exception):
    def __init__(self, status_code: int):
        super().__init__(f"Error code: {status_code}")
        self.status_code = status_code


def test_is_transient_classifies_errors():
    assert is_transient(_StatusError(503))
    assert is_transient(_StatusError(429))
    assert not is_transient(_StatusError(400))
    assert not is_transient(_StatusError(401))
    assert is_transient(Exception("Error code: 503 - {'code': 'service_unavailable'}"))
    assert not is_transient(Exception("Error code: 403 - permission denied"))
    assert is_transient(Exception("model is currently experiencing high demand"))
    assert not is_transient(ValueError("bad schema"))


DAILY_QUOTA_MESSAGE = (
    "Error code: 429 - Rate limit exceeded for model gemini-3.8-flash "
    "(limit: 20 requests per day on Free Tier). Please retry in 8h58m13s"
)


class _DailyQuotaError(Exception):
    status_code = 429


def test_daily_quota_exhaustion_is_not_transient():
    assert not is_transient(Exception(DAILY_QUOTA_MESSAGE))
    assert not is_transient(_DailyQuotaError(DAILY_QUOTA_MESSAGE))
    # A short per-minute rate limit is still worth retrying.
    assert is_transient(_StatusError(429))


def test_daily_quota_is_not_retried():
    calls = []

    def exhausted():
        calls.append(1)
        raise _DailyQuotaError(DAILY_QUOTA_MESSAGE)

    with pytest.raises(_DailyQuotaError):
        call_with_retry(exhausted, label="t", sleep=lambda _: None)
    assert len(calls) == 1


class ReadTimeout(Exception):
    pass


def test_timeouts_are_transient():
    assert is_transient(ReadTimeout())
    assert is_transient(Exception("The read operation timed out"))


def test_retries_transient_then_succeeds():
    calls = []
    delays = []

    def flaky():
        calls.append(1)
        if len(calls) < 3:
            raise _StatusError(503)
        return "ok"

    assert call_with_retry(flaky, label="t", sleep=delays.append) == "ok"
    assert len(calls) == 3
    assert delays == [10.0, 20.0]


def test_non_transient_error_is_not_retried():
    calls = []

    def bad():
        calls.append(1)
        raise _StatusError(401)

    with pytest.raises(_StatusError):
        call_with_retry(bad, label="t", sleep=lambda _: None)
    assert len(calls) == 1


def test_gives_up_after_attempts():
    calls = []

    def always():
        calls.append(1)
        raise _StatusError(503)

    with pytest.raises(_StatusError):
        call_with_retry(always, label="t", attempts=3, sleep=lambda _: None)
    assert len(calls) == 3
