from pathlib import Path

from morning_radio.kakao_auth import generate_encryption_key, load_refresh_token, store_refresh_token


def test_kakao_refresh_token_roundtrip(tmp_path: Path):
    path = tmp_path / "auth.json"
    key = generate_encryption_key()
    store_refresh_token("refresh-token-value", key, path)
    assert load_refresh_token(key, path) == "refresh-token-value"
    assert "refresh-token-value" not in path.read_text(encoding="utf-8")
