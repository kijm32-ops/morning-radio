# MORNING RADIO

WORLD BRIEFING + MORNING BRIEFING + PTIS 결과를 바탕으로 **보고서를 낭독하지 않고, 두 AI 진행자가 연결·해석·반론을 주고받는 출근길 팟캐스트**를 자동 생성하는 프로젝트입니다.

## v0.1 목표

`Gmail 최종 결과 수집 → Gemini Director → 2인 대화 대본 → Gemini 3.8 Flash TTS → MP3 → 모바일 플레이어 → Kakao '출근길에 듣기'`

기존 WORLD/MORNING/PTIS 프로젝트는 수정하지 않습니다. 세 시스템이 이미 보내는 최종 메일을 읽기 때문에 MORNING RADIO가 실패해도 기존 브리핑에는 영향이 없습니다.

## 설계 원칙

- 보고서별 순차 낭독 금지. 세 소스를 하나의 취재자료 묶음으로 사용합니다.
- `사실 → 연결 → 해석 → 반론/다른 가능성 → 관찰 포인트`로 대화합니다.
- 사실과 AI 해석/가설을 언어적으로 구분합니다.
- 정치 이슈는 사실·정책 효과·상반된 해석을 중립적으로 다루며 정치적 선택을 권하지 않습니다.
- 투자 매수/매도 지시를 하지 않습니다.
- 소스 하나가 실패해도 나머지 소스로 partial success가 가능합니다. 세 소스 모두 실패할 때만 중단합니다.

## 현재 모델

- Director: `gemini-3.8-flash`, `thinking_level=high`
- Voice: `gemini-3.8-flash-tts`
- TTS mode: `conversational`, 2 speakers
- 기본 Voice: Host A=`Puck`, Host B=`Kore`

## 실행 전 GitHub Secrets

Repository → Settings → Secrets and variables → Actions → Secrets에 아래 값을 등록합니다.

- `GEMINI_API_KEY`
- `GMAIL_USER`
- `GMAIL_APP_PASSWORD` — Gmail 앱 비밀번호
- `KAKAO_REST_API_KEY`
- `KAKAO_REFRESH_TOKEN`
- `KAKAO_CLIENT_SECRET` — 사용하는 Kakao 앱이 Client Secret을 켠 경우

Actions Variables에는 필요 시 `PLAYER_BASE_URL`을 등록할 수 있습니다. 실제 workflow는 Pages 배포 결과 URL을 우선 사용합니다.

## Gmail 수집 방식

최근 메일 중 다음 제목 조각을 찾습니다.

- WORLD: `WORLD BRIEFING`
- Morning: `모닝 브리핑`
- PTIS: `[PTIS]`

WORLD처럼 PDF가 첨부되어 있으면 PDF를 직접 읽습니다. Morning처럼 메일 본문에 Google Drive PDF 링크가 있으면 공개 링크를 내려받아 읽습니다. PTIS처럼 HTML 본문 자체에 결과가 있으면 본문을 사용합니다.

환경변수 `WORLD_SUBJECT`, `MORNING_SUBJECT`, `PTIS_SUBJECT`로 제목 조각을 변경할 수 있습니다.

## 로컬 dry run

```bash
set -e
python -m venv .venv
source .venv/bin/activate  # Windows PowerShell: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
pytest -q

mkdir -p data/inbox
# data/inbox/world.txt, morning.txt, ptis.txt 준비
python -m morning_radio.main --source-mode directory --plan-only
```

실제 TTS까지 만들려면 `--plan-only`를 제거하고 ffmpeg가 PATH에 있어야 합니다.

## 첫 운영 테스트

1. GitHub Secrets를 등록합니다.
2. 이 저장소가 Private인 경우 GitHub Pages는 GitHub Pro 이상에서 사용할 수 있습니다. GitHub Free라면 repo를 Public으로 바꾸거나 별도 정적 호스팅을 붙여야 합니다.
3. Settings → Pages에서 GitHub Actions를 source로 사용하도록 설정합니다.
4. Actions → **Build Morning Radio** → Run workflow를 수동 실행합니다.
5. 생성된 Pages의 오디오를 확인하고, 마지막 단계에서 Kakao '▶ 출근길에 듣기' 메시지가 오는지 확인합니다.

## 아직 자동 07:30 스케줄을 켜지 않은 이유

GitHub Actions `schedule`은 정확한 시각 실행을 보장하지 않습니다. 먼저 수동 end-to-end 테스트로 대본·음성·수집 안정성을 검증한 뒤, 운영판에서는 Cloud Scheduler가 07:30 KST 알림을 담당하도록 분리할 예정입니다.

## 실패 정책

- WORLD만 실패 → MORNING + PTIS로 생성
- MORNING만 실패 → WORLD + PTIS로 생성
- PTIS만 실패 → WORLD + MORNING으로 생성
- 모두 실패 → 생성 중단, 깨진 플레이어/카카오 링크를 발송하지 않음
- TTS segment 하나 실패 → 전체 배포 중단(다음 버전에서 segment retry 추가 예정)

## Kakao refresh token 주의

Kakao 토큰 갱신 응답에서 새 `refresh_token`이 발급되는 경우 workflow가 경고를 출력합니다. v0.1은 GitHub Secret을 자동 변경하지 않으므로 해당 경우 `KAKAO_REFRESH_TOKEN` Secret을 갱신해야 합니다. 이 부분은 운영 자동화 단계에서 암호화된 token state로 개선합니다.
