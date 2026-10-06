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
