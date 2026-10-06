# Project

## Purpose

MORNING RADIO. WORLD BRIEFING, MORNING BRIEFING, PTIS 결과를 바탕으로 두 AI 진행자가 연결·해석·반론을 주고받는 출근길 팟캐스트를 생성한다. 이 저장소는 비공개(private)다.

## Architecture

- Frontend: 모바일 플레이어 (README 파이프라인에 포함, `tests/test_player.py`가 검증)
- Backend: Python 파이프라인 `Gmail → Gemini Director → 2인 대화 → Gemini TTS → MP3 → mobile player → Kakao`. 모델은 README 기준 Director `gemini-3.8-flash`, Voice `gemini-3.8-flash-tts`
- Database: 없음. `data/` 디렉터리가 있다 (내용은 확인하지 않았다)

## Important directories

- `morning_radio/` — 파이프라인 소스
- `tests/` — pytest (`test_kakao_auth`, `test_models`, `test_player`, `test_sources`)
- `data/` — 런타임 데이터
- `.github/workflows/` — `build-radio.yml`, `validate.yml`
- `.env.example` — 환경변수 목록 (실제 `.env`는 올리지 않는다)

## Environments

### Development

- Python. CI는 3.12를 쓴다. 로컬 설치 상태는 확인하지 않았다.

### Production / Deployment target

- GitHub Actions(`build-radio.yml`, 정확한 동작은 확인하지 않았다)와 Kakao 전달. README 파이프라인 기준.

## Invariants

- 기존 WORLD / MORNING / PTIS 프로젝트는 수정하지 않는다(README 기준).
- 한 소스가 실패해도 나머지로 부분 성공하며, 세 소스가 모두 실패할 때만 생성하지 않는다. 이 동작을 깨지 않는다.
- Kakao refresh token은 회전한다. 회전된 토큰을 저장하는 동작(`fix: persist Kakao refresh-token rotation`)을 깨지 않는다.
- `.env`, API 키, Kakao 토큰, Gmail 인증 정보를 읽어서 출력하거나 commit하지 않는다.
