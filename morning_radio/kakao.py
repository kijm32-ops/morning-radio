from __future__ import annotations

import json

import requests

from .config import Settings
from .models import EpisodePlan


class KakaoError(RuntimeError):
    pass


def _access_token(settings: Settings) -> tuple[str, str | None]:
    if not settings.kakao_rest_api_key or not settings.kakao_refresh_token:
        raise KakaoError("KAKAO_REST_API_KEY / KAKAO_REFRESH_TOKEN이 필요합니다.")
    data = {
        "grant_type": "refresh_token",
        "client_id": settings.kakao_rest_api_key,
        "refresh_token": settings.kakao_refresh_token,
    }
    if settings.kakao_client_secret:
        data["client_secret"] = settings.kakao_client_secret
    response = requests.post("https://kauth.kakao.com/oauth/token", data=data, timeout=20)
    response.raise_for_status()
    payload = response.json()
    token = payload.get("access_token")
    if not token:
        raise KakaoError("Kakao token 응답에 access_token이 없습니다.")
    return token, payload.get("refresh_token")


def send_ready_message(settings: Settings, plan: EpisodePlan, player_url: str | None = None) -> str | None:
    url = (player_url or settings.player_base_url).strip()
    if not url:
        raise KakaoError("PLAYER_BASE_URL이 필요합니다.")
    token, rotated_refresh_token = _access_token(settings)
    description = f"{plan.teaser}\n약 {plan.target_minutes}분 · 오늘의 핵심 이야기 {len(plan.segments)}개"
    template = {
        "object_type": "text",
        "text": f"🎙️ 오늘 아침 AI RADIO가 준비됐습니다.\n\n{plan.title}\n{description}",
        "link": {"web_url": url, "mobile_web_url": url},
        "button_title": "▶ 출근길에 듣기",
    }
    response = requests.post(
        "https://kapi.kakao.com/v2/api/talk/memo/default/send",
        headers={"Authorization": f"Bearer {token}"},
        data={"template_object": json.dumps(template, ensure_ascii=False)},
        timeout=20,
    )
    response.raise_for_status()
    if response.json().get("result_code") != 0:
        raise KakaoError(f"Kakao message 실패: {response.text}")
    return rotated_refresh_token
