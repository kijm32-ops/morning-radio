import json
import threading
import time
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest
from google.genai import types

from morning_radio.gemini import make_client


def test_client_has_sdk_retries_disabled():
    client = make_client("test-key")
    # The SDK must not sleep on Retry-After; retry.call_with_retry owns retrying.
    assert client.interactions.sdk_configuration.retry_config.max_retries == 0


def test_rate_limit_with_retry_after_fails_fast():
    hits: list[float] = []

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            self.rfile.read(int(self.headers.get("Content-Length", 0)))
            hits.append(time.time())
            body = json.dumps(
                {"error": {"code": 429, "message": "quota", "status": "RESOURCE_EXHAUSTED"}}
            ).encode()
            self.send_response(429)
            self.send_header("Content-Type", "application/json")
            self.send_header("Retry-After", "60")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *args):
            return

    server = HTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        client = make_client(
            "test-key",
            http_options=types.HttpOptions(base_url=f"http://127.0.0.1:{server.server_port}"),
        )
        started = time.time()
        with pytest.raises(Exception) as excinfo:
            client.interactions.create(model="m", input="hi", timeout=5.0)
        assert time.time() - started < 5
        assert len(hits) == 1
        assert "RateLimit" in type(excinfo.value).__name__
    finally:
        server.shutdown()
        server.server_close()
