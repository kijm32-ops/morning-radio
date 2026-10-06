from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

from google import genai

from .config import Settings
from .models import EpisodePlan, SourceDocument
from .retry import call_with_retry

KST = ZoneInfo("Asia/Seoul")
# 응답이 없는 호출이 Actions 작업을 무한정 붙잡지 않도록 요청마다 제한한다.
DIRECTOR_TIMEOUT_SECONDS = 600.0


DIRECTOR_RULES = """
당신은 'MORNING RADIO'의 팟캐스트 디렉터다.
세 개의 자동화 결과(WORLD BRIEFING, MORNING BRIEFING, PTIS)는 낭독용 원고가 아니라 취재 자료다.

목표:
- 한국어 2인 대화형 출근길 팟캐스트를 만든다.
- 보고서 1, 2, 3 순서로 읽지 않는다. 서로 관련된 사실을 자유롭게 연결한다.
- 사실 → 연결 → 해석 → 반론/다른 가능성 → 오늘 확인할 관찰 포인트의 흐름을 만든다.
- 진행자 A는 맥락과 연결을 적극적으로 제시하고, 진행자 B는 반론·대안 설명·불확실성을 짚는다.
- 두 진행자가 항상 합의할 필요는 없다. 단, 근거 없는 논쟁을 만들지 않는다.
- '보고서에 따르면'이라는 표현을 반복하지 말고 자연스러운 대화로 풀어낸다.
- 숫자는 중요한 것만 말하고, 숫자의 의미를 설명한다.
- 같은 사건이 WORLD와 MORNING에 모두 있으면 중복 낭독하지 말고 교차 검증·연결의 재료로 쓴다.
- PTIS는 실제로 흥미로운 딜이 있을 때만 자연스럽게 화제로 가져온다. 특가가 없으면 짧게 끝낸다.
- 자료에 없는 구체적 사실을 만들지 않는다.
- 사실과 해석/가설을 언어적으로 구분한다. 가설은 '가능성이 있다', '한 가지 설명은' 등의 표현을 쓴다.
- 투자 매수·매도 지시, 특정 정치인·정당·정책에 대한 지지/반대 권유, 선거 선택 권유를 하지 않는다.
- 정치 이슈는 확인된 사실, 정책·시장 영향, 상반된 해석과 불확실성을 중립적으로 다룬다.
- 청취자는 기본적인 경제·시사 용어를 이해한다고 가정한다. 교과서식 기초 설명은 피한다.
- 말투는 뉴스 앵커가 아니라 경제·국제뉴스를 좋아하는 두 사람이 커피를 마시며 이야기하는 정도로 자연스럽게 한다.
- 과한 감탄사, 억지 유머, 반복되는 인사말을 피한다.

구성:
- 4~6개 segment.
- 첫 30~45초 안에 오늘 가장 흥미로운 질문을 던진다.
- 전체 길이는 target_minutes에 근접하도록 충분한 대화량을 만든다.
- segment마다 6~16개의 turn을 권장한다.
- 마지막은 예측 단정이 아니라 오늘 무엇을 보면 해석이 강화/약화되는지 정리한다.
""".strip()


def _source_block(doc: SourceDocument) -> str:
    text = doc.text.strip()
    if len(text) > 45_000:
        text = text[:45_000] + "\n...[source truncated]"
    return (
        f"\n===== {doc.source.upper()} / {doc.status.upper()} =====\n"
        f"captured_at: {doc.captured_at.isoformat()}\n"
        f"origin: {doc.origin}\n"
        f"{text}\n"
    )


def build_episode_plan(settings: Settings, sources: list[SourceDocument]) -> EpisodePlan:
    if not settings.gemini_api_key:
        raise RuntimeError("GEMINI_API_KEY가 필요합니다.")

    usable = [doc for doc in sources if doc.status != "failed" and doc.text.strip()]
    if not usable:
        raise RuntimeError("사용 가능한 소스가 하나도 없습니다.")

    today = datetime.now(KST).date().isoformat()
    source_text = "\n".join(_source_block(doc) for doc in sources)
    prompt = f"""{DIRECTOR_RULES}

오늘 날짜: {today}
target_minutes: {settings.target_minutes}

아래 자료만 근거로 EpisodePlan을 작성하라.
각 turn의 evidence에는 근거가 된 source 이름(world/morning/ptis)을 넣어라.
TTS가 그대로 읽을 text이므로 speaker label이나 괄호형 무대지시를 text에 넣지 마라.
style은 짧은 영어 구문으로 작성해도 된다.

{source_text}
"""

    client = genai.Client(api_key=settings.gemini_api_key)
    interaction = call_with_retry(
        lambda: client.interactions.create(
            model=settings.director_model,
            input=prompt,
            response_format={
                "type": "text",
                "mime_type": "application/json",
                "schema": EpisodePlan.model_json_schema(),
            },
            generation_config={"thinking_level": "high"},
            timeout=DIRECTOR_TIMEOUT_SECONDS,
        ),
        label="director",
    )
    return EpisodePlan.model_validate_json(interaction.output_text)
