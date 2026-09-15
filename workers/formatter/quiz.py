"""
D — 객관식 + 단답형 필수, True/False 선택 허용 복습 퀴즈 + 해설.

연동:
    읽음 ← schemas.state.AgentState
    읽음 ← C 분석 산출
    씀 → schemas.quiz.QuizItem
    읽힘 → workers/formatter/markdown.py, graph/verify.py, ui/tabs.py

LLM:
    config.get_chat_model(role="generate")
"""

from __future__ import annotations

import json

from pydantic import BaseModel, model_validator

from config import get_chat_model
from schemas.quiz import QuizItem
from schemas.state import AgentState


class QuizLLMOutput(BaseModel):
    """Gemini가 반환할 복습 퀴즈 전체 출력 구조입니다.

    Attributes:
        quiz_items: 객관식과 단답형을 필수로 포함하고,
            True/False를 선택적으로 포함할 수 있는 복습 퀴즈 목록.
    """

    quiz_items: list[QuizItem]

    @model_validator(mode="after")
    def validate_quiz_type_mix(self) -> QuizLLMOutput:
        """객관식과 단답형이 모두 포함되었는지 검사합니다.

        Returns:
            유형 검증을 통과한 QuizLLMOutput.

        Raises:
            ValueError: 객관식 또는 단답형이 하나도 없는 경우.
        """

        quiz_types = {item.quiz_type for item in self.quiz_items}

        if "mcq" not in quiz_types:
            raise ValueError("복습 퀴즈에는 객관식(mcq)이 하나 이상 필요합니다.")

        if "short" not in quiz_types:
            raise ValueError("복습 퀴즈에는 단답형(short)이 하나 이상 필요합니다.")

        return self


def _serialize_items(
    items: list[BaseModel | dict],
) -> list[dict]:
    """State 내부 객체를 JSON 직렬화 가능한 형태로 변환합니다.

    Pydantic 모델은 model_dump()를 사용해 딕셔너리로 변환하고,
    이미 딕셔너리인 값은 그대로 사용합니다.

    Args:
        items: Pydantic 모델 또는 딕셔너리 목록.

    Returns:
        JSON 직렬화가 가능한 딕셔너리 목록.
    """

    serialized = []

    for item in items:
        if isinstance(
            item,
            BaseModel,
        ):
            serialized.append(item.model_dump())
        else:
            serialized.append(item)

    return serialized


def _build_quiz_evidence(
    state: AgentState,
) -> dict:
    """C 분석 결과에서 퀴즈 생성 근거를 추출합니다.

    Args:
        state: 현재 LangGraph AgentState.

    Returns:
        퀴즈 생성에 사용할 C 분석 결과 딕셔너리.
    """

    return {
        "concepts": _serialize_items(
            state.get(
                "concepts",
                [],
            )
        ),
        "code_units": _serialize_items(
            state.get(
                "code_units",
                [],
            )
        ),
        "flows": _serialize_items(
            state.get(
                "flows",
                [],
            )
        ),
        "tables": _serialize_items(
            state.get(
                "tables",
                [],
            )
        ),
        "cross_references": _serialize_items(
            state.get(
                "cross_references",
                [],
            )
        ),
        "practice_notes": _serialize_items(
            state.get(
                "practice_notes",
                [],
            )
        ),
    }


def _collect_source_chunk_ids(
    evidence: dict,
) -> list[str]:
    """C 분석 결과에서 사용할 수 있는 출처 Chunk ID를 수집합니다.

    Args:
        evidence: C 분석 결과 딕셔너리.

    Returns:
        중복이 제거된 source_chunk_ids 목록.
    """

    source_chunk_ids = []

    for items in evidence.values():
        for item in items:
            for chunk_id in item.get(
                "source_chunk_ids",
                [],
            ):
                if chunk_id not in source_chunk_ids:
                    source_chunk_ids.append(chunk_id)

    return source_chunk_ids


def _build_quiz_prompt(
    evidence: dict,
    source_chunk_ids: list[str],
) -> str:
    """C 분석 결과를 기반으로 퀴즈 생성 프롬프트를 작성합니다.

    Args:
        evidence: C 분석 결과 딕셔너리.
        source_chunk_ids: 퀴즈에서 사용할 수 있는 출처 Chunk ID 목록.

    Returns:
        Gemini에 전달할 퀴즈 생성 프롬프트.
    """

    evidence_json = json.dumps(
        evidence,
        ensure_ascii=False,
        indent=2,
    )

    source_ids_json = json.dumps(
        source_chunk_ids,
        ensure_ascii=False,
        indent=2,
    )

    return f"""
당신은 제공된 학습 분석 결과만을 근거로
복습 퀴즈를 생성하는 AI입니다.

[학습 분석 결과]
{evidence_json}

[사용 가능한 source_chunk_ids]
{source_ids_json}

[생성 규칙]

1. 제공된 학습 분석 결과에 없는 사실을
   추가하거나 추측하지 마세요.

2. 객관식(mcq)과 단답형(short)은
   반드시 모두 포함하세요.

3. true_false 유형은 필요한 경우
   선택적으로 추가할 수 있습니다.
   true_false의 answer는 "True" 또는 "False"로 작성하세요.
   options는 필요하지 않으며, 사용할 경우 ["True", "False"]로 작성하세요.

4. 객관식 문제에는 options를 작성하세요.

5. 객관식의 answer는 번호나 알파벳이 아니라
   options 안에 있는 보기 문자열과 정확히 같아야 합니다.

6. 단답형 문제의 options는 빈 리스트로 작성하세요.

7. 모든 문제에는 다음 필드를 작성하세요.
   - quiz_type
   - question
   - options
   - answer
   - explanation
   - source_chunk_ids

8. explanation은 제공된 학습 분석 결과를 근거로
   정답을 설명하세요.

9. source_chunk_ids에는 위에 제공된
   사용 가능한 ID만 사용하세요.

10. 존재하지 않는 source_chunk_id를
    새로 만들지 마세요.

11. 같은 내용을 표현만 바꾸어
    반복해서 출제하지 마세요.
"""


def produce_quiz_items(
    state: AgentState,
) -> list[QuizItem]:
    """C 분석 결과를 기반으로 복습 퀴즈를 생성합니다.

    객관식과 단답형을 필수로 포함하고,
    True/False 문제를 선택적으로 추가할 수 있습니다.

    Args:
        state: C 분석 결과가 포함된 AgentState.

    Returns:
        Pydantic 검증을 통과한 QuizItem 목록.

    Raises:
        ValueError: 퀴즈를 생성할 C 분석 결과가 없거나,
            사용할 source_chunk_ids가 없거나,
            허용되지 않은 source_chunk_id가 포함된 경우.
    """

    evidence = _build_quiz_evidence(state)

    has_analysis = any(evidence.values())

    if not has_analysis:
        raise ValueError("복습 퀴즈를 생성할 C 분석 결과가 없습니다.")

    source_chunk_ids = _collect_source_chunk_ids(evidence)

    if not source_chunk_ids:
        raise ValueError("복습 퀴즈의 근거로 사용할 source_chunk_ids가 없습니다.")

    prompt = _build_quiz_prompt(
        evidence,
        source_chunk_ids,
    )

    model = get_chat_model(role="generate")

    structured_model = model.with_structured_output(QuizLLMOutput)

    result = structured_model.invoke(prompt)

    allowed_source_ids = set(source_chunk_ids)

    for item in result.quiz_items:
        invalid_source_ids = set(item.source_chunk_ids) - allowed_source_ids

        if invalid_source_ids:
            raise ValueError("퀴즈에 허용되지 않은 source_chunk_ids가 포함되어 있습니다.")

    return result.quiz_items
