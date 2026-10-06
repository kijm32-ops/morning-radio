# Validation

아래는 `.github/workflows/validate.yml`이 실제로 실행하는 검증이다.

## Pre-check

- `git status`
- placeholder 검사: `<REQUIRED:`

## Backend

- `pip install -r requirements.txt`
- `python -m compileall -q morning_radio tests`
- `python -m pytest -q`

## Frontend

- `tests/test_player.py`가 플레이어를 검증한다 (위 pytest에 포함).

## Database

- 없음

## Final

- `git diff --check`
- `git diff`
- 예상 외 파일 변경 여부 확인
- 비밀값이 diff에 섞이지 않았는지 확인
