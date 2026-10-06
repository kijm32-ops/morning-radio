# Validation

?꾨옒??`.github/workflows/validate.yml`???ㅼ젣濡??ㅽ뻾?섎뒗 寃利앹씠??

## Pre-check

- `git status`
- placeholder 寃?? `<REQUIRED:`

## Backend

- `pip install -r requirements.txt`
- `python -m compileall -q morning_radio tests`
- `python -m pytest -q`

## Frontend

- `tests/test_player.py`媛 ?뚮젅?댁뼱瑜?寃利앺븳??(??pytest???ы븿).

## Database

- ?놁쓬

## Final

- `git diff --check`
- `git diff`
- ?덉긽 ???뚯씪 蹂寃??щ? ?뺤씤
- 鍮꾨?媛믪씠 diff???욎씠吏 ?딆븯?붿? ?뺤씤
