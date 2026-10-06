from __future__ import annotations

from google import genai
from google.genai import types


def make_client(api_key: str, http_options: types.HttpOptions | None = None) -> genai.Client:
    """Gemini client with the SDK's built-in retries disabled.

    The SDK retries internally and sleeps for the server's ``Retry-After`` value with
    no upper bound, so a single 429/503 can stall a run for an hour regardless of the
    per-request timeout. Retrying is handled by ``retry.call_with_retry`` instead,
    which caps the delay.

    ``HttpRetryOptions(attempts=0)`` is not enough: the SDK maps it to one retry. The
    retry config is therefore set directly (google-genai is pinned in requirements.txt;
    ``tests/test_gemini.py`` fails if an upgrade changes this).
    """
    client = genai.Client(api_key=api_key, http_options=http_options)
    client.interactions.sdk_configuration.retry_config.max_retries = 0
    return client
