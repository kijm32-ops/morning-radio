# MORNING RADIO

WORLD BRIEFING + MORNING BRIEFING + PTIS 결과를 바탕으로, 두 AI 진행자가 연결·해석·반론을 주고받는 출근길 팟캐스트를 생성합니다.

## Pipeline

`Gmail → Gemini Director → 2인 대화 → Gemini TTS → MP3 → mobile player → Kakao`

기존 WORLD/MORNING/PTIS 프로젝트는 수정하지 않습니다. 한 소스가 실패해도 나머지 소스로 부분 성공하며, 세 소스가 모두 실패할 때만 생성하지 않습니다.

## Models

- Director: `gemini-3.8-flash`, high thinking
- Voice: `gemini-3.8-flash-tts`
- TTS: conversational, 2 speakers
- Host A: Puck
- Host B: Kore

## GitHub Actions secrets

필수:

- `GEMINI_API_KEY`
- `GMAIL_USER`
- `GMAIL_APP_PASSWORD`
- `KAKAO_REST_API_KEY`
- `KAKAO_CLIENT_SECRET`
- `KAKAO_TOKEN_ENCRYPTION_KEY`

`KAKAO_REFRESH_TOKEN`은 GitHub Secret에 저장하지 않습니다. `data/kakao_auth.json`에 Fernet으로 암호화해 저장하며, Actions가 카카오 토큰 회전 시 암호화 파일을 자동 갱신·커밋합니다.

Actions Variables는 v0.1에서 필수가 없습니다.

## Kakao one-time setup

MORNING RADIO 전용 Kakao Developers 앱 사용을 권장합니다.

앱 설정:

1. Kakao Login 활성화
2. REST API key Redirect URI에 `http://127.0.0.1:8765/callback` 등록
3. Consent items에서 `talk_message` 활성화
4. REST API key의 Client Secret 활성화
5. Product Link web domain에 실제 플레이어 도메인 등록

로컬 설정:

```powershell
python -m pip install -r requirements.txt
python setup_kakao.py --print-encryption-key
```

출력된 Fernet key는 GitHub Secret `KAKAO_TOKEN_ENCRYPTION_KEY`로 저장합니다. 같은 값을 아래 로컬 환경변수에도 사용합니다.

```powershell
$env:KAKAO_REST_API_KEY="..."
$env:KAKAO_CLIENT_SECRET="..."
$env:KAKAO_TOKEN_ENCRYPTION_KEY="..."
$env:KAKAO_REDIRECT_URI="http://127.0.0.1:8765/callback"
python setup_kakao.py
```

브라우저에서 MORNING RADIO가 카카오톡 메시지를 보낼 수 있도록 동의하면 `data/kakao_auth.json`이 생성됩니다. 이 파일은 암호화된 토큰만 포함합니다.

```powershell
git add data/kakao_auth.json
git commit -m "chore: initialize Kakao OAuth state"
git push
```

평문 refresh token, Client Secret, encryption key는 절대 커밋하지 않습니다.

## Gmail collection

최근 메일에서 제목 조각으로 세 소스를 찾습니다.

- WORLD: `WORLD BRIEFING`
- Morning: `모닝 브리핑`
- PTIS: `[PTIS]`

첨부 PDF가 있으면 PDF를 읽고, Gmail 본문에 Drive PDF 링크가 있으면 해당 PDF를 내려받습니다. PTIS처럼 HTML 본문에 결과가 있으면 본문을 사용합니다.

## First run

1. GitHub Actions Secrets를 등록합니다.
2. Kakao one-time setup으로 `data/kakao_auth.json`을 생성·push합니다.
3. GitHub Pages를 활성화합니다.
4. Actions → Build Morning Radio → Run workflow를 실행합니다.
5. Pages 플레이어, 실제 오디오, Kakao `▶ 출근길에 듣기` 버튼을 확인합니다.

07:30 자동 실행은 수동 end-to-end 검증 후 별도 정확한 스케줄러로 활성화합니다.
