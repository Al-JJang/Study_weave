"""
A — 검증 에이전트 (팀장, 그래프 설계까지).

검사 초안:
    1. source_chunk_ids 가 parsed/retrieved chunk 에 존재
    2. mcq answer 가 options 안에 있음
    3. route 에 맞는 C/D 섹션이 비어 있지 않음
    4. retryable 이면 errors 에 넣고 supervisor 가 재실행

연동:
    import ← schemas.*, config.NODE_FAILURE_POLICY
    불림 → graph/supervisor.py (node "verify")
    선택 LLM → config.get_chat_model(role="verify")
"""

from __future__ import annotations

import itertools

import config
from schemas.errors import ErrorCode, NodeError, VerificationReport
from schemas.quiz import QuizItem
from schemas.state import AgentState


def collect_known_chunk_ids(state: AgentState) -> set[str]:
    """파싱되거나 검색된 모든 청크의 ID 집합을 추출합니다.

    Args:
        state: parsed_chunks 와 retrieved_chunks 를 포함한 AgentState.

    Returns:
        parsed_chunks 와 retrieved_chunks 에 존재하는 모든 chunk_id 의 집합.
    """
    parsed_chunks = state.get("parsed_chunks") or []
    retrieved_chunks = state.get("retrieved_chunks") or []
    return {chunk.chunk_id for chunk in itertools.chain(parsed_chunks, retrieved_chunks)}


def validate_citations(state: AgentState) -> list[tuple[ErrorCode, str]]:
    """C/D 섹션 생성 항목의 source_chunk_ids가 실제 존재하는 청크 ID인지 검증합니다.

    Args:
        state: concepts/code_units/flows/tables/cross_references/
            practice_notes/quiz_items 및 parsed_chunks, retrieved_chunks 를
            포함한 AgentState.

    Returns:
        (error_code, message) 튜플 목록. CITATION_MISSING 또는
        HALLUCINATED_CHUNK_ID 이슈를 설명. 문제가 없으면 빈 리스트.
    """
    known_ids = collect_known_chunk_ids(state)
    issues: list[tuple[ErrorCode, str]] = []

    sections = [
        ("concepts", state.get("concepts") or []),
        ("code_units", state.get("code_units") or []),
        ("flows", state.get("flows") or []),
        ("tables", state.get("tables") or []),
        ("cross_references", state.get("cross_references") or []),
        ("practice_notes", state.get("practice_notes") or []),
        ("quiz_items", state.get("quiz_items") or []),
    ]

    for section_name, items in sections:
        for idx, item in enumerate(items):
            chunk_ids = item.source_chunk_ids

            if not chunk_ids:
                issues.append(
                    (
                        "CITATION_MISSING",
                        f"[{section_name.upper()}_INDEX_{idx}] CITATION_MISSING: "
                        f"source_chunk_ids is missing or empty.",
                    )
                )
                continue

            for cid in chunk_ids:
                if cid not in known_ids:
                    issues.append(
                        (
                            "HALLUCINATED_CHUNK_ID",
                            f"[{section_name.upper()}_INDEX_{idx}] HALLUCINATED_CHUNK_ID: "
                            f"Chunk ID '{cid}' is hallucinated (not found in parsed/retrieved chunks).",
                        )
                    )

    return issues


def validate_quiz_items(
    items: list[QuizItem],
) -> tuple[list[QuizItem], list[int], list[tuple[ErrorCode, str]]]:
    """퀴즈 문항의 타입 및 정합성을 검증하고, 유효하지 않은 퀴즈를 필터링합니다.

    Args:
        items: 검증할 퀴즈 문항 목록.

    Returns:
        (valid_items, dropped_quiz_ids, issues) 튜플.
            valid_items: 검증을 통과한 퀴즈 문항만 남긴 목록.
            dropped_quiz_ids: 검증에 실패해 제외된 문항의 원본 인덱스 목록.
            issues: (error_code, message) 튜플 목록.
    """
    valid_items = []
    dropped_quiz_ids = []
    issues: list[tuple[ErrorCode, str]] = []

    for i, item in enumerate(items):
        qtype = item.quiz_type
        qanswer = item.answer
        qoptions = item.options

        if qtype == "mcq":
            if not qoptions:
                issues.append(
                    (
                        "QUIZ_ANSWER_MISMATCH",
                        f"[QUIZ_INDEX_{i}] QUIZ_ANSWER_MISMATCH: MCQ options are empty.",
                    )
                )
                dropped_quiz_ids.append(i)
            elif qanswer not in qoptions:
                issues.append(
                    (
                        "QUIZ_ANSWER_MISMATCH",
                        f"[QUIZ_INDEX_{i}] QUIZ_ANSWER_MISMATCH: "
                        f"Answer '{qanswer}' is not in options: {qoptions}",
                    )
                )
                dropped_quiz_ids.append(i)
            else:
                valid_items.append(item)
        elif qtype == "true_false":
            if qanswer not in ("True", "False"):
                issues.append(
                    (
                        "QUIZ_ANSWER_MISMATCH",
                        f"[QUIZ_INDEX_{i}] QUIZ_ANSWER_MISMATCH: "
                        f"True/False answer must be 'True' or 'False'. Found '{qanswer}'",
                    )
                )
                dropped_quiz_ids.append(i)
            else:
                valid_items.append(item)
        else:
            # short-answer 및 기타 유형은 통과
            valid_items.append(item)

    return valid_items, dropped_quiz_ids, issues


def validate_route_outputs(state: AgentState) -> list[tuple[ErrorCode, str]]:
    """라우팅 결과에 따라 필수 섹션(C/D)이 적절하게 채워졌는지 검사합니다.

    Args:
        state: route 와 concepts/code_units/cross_references 를 포함한
            AgentState.

    Returns:
        route 에 따라 필수인 섹션이 비어 있을 때 (error_code, message) 튜플을
        담은 목록. 문제가 없으면 빈 리스트.
    """
    issues: list[tuple[ErrorCode, str]] = []
    route = state.get("route", "both")

    if route == "pdf_only":
        if not state.get("concepts"):
            issues.append(("EMPTY_SECTION", "[EMPTY_SECTION] pdf_only route has empty concepts."))
    elif route == "code_only":
        if not state.get("code_units"):
            issues.append(
                ("EMPTY_SECTION", "[EMPTY_SECTION] code_only route has empty code_units.")
            )
    elif route == "both" and not state.get("cross_references"):
        issues.append(("EMPTY_SECTION", "[EMPTY_SECTION] both route has empty cross_references."))

    return issues


def verify_node(state: AgentState) -> dict:
    """citation / quiz / route 검사를 모아 검증 결과로 AgentState 를 갱신합니다.

    Args:
        state: 검증 대상 AgentState. quiz_items, concepts, code_units,
            cross_references, route, retry_count, errors 등을 참조합니다.

    Returns:
        AgentState 를 갱신할 딕셔너리. 반환 key:
            verification: 검증 결과를 담은 VerificationReport.
            quiz_items: 검증을 통과한 퀴즈 문항만 남긴 목록.
            status: 모든 검사를 통과했으면 "completed", 아니면 "failed".
            errors: 기존 errors 에 이번 검증에서 발견된 NodeError 를 이어붙인
                목록.
            retry_count: 실패했으면 1 증가, 통과했으면 그대로.
    """
    citation_issues = validate_citations(state)
    route_issues = validate_route_outputs(state)

    raw_quiz_items = state.get("quiz_items") or []
    valid_quiz_items, dropped_quiz_ids, quiz_issues = validate_quiz_items(raw_quiz_items)

    all_issues = citation_issues + route_issues + quiz_issues
    passed = len(all_issues) == 0

    report = VerificationReport(
        passed=passed,
        issues=[message for _, message in all_issues],
        dropped_quiz_ids=dropped_quiz_ids,
    )

    status = "completed" if passed else "failed"
    errors = list(state.get("errors") or [])
    retry_count = state.get("retry_count", 0)

    if not passed:
        retryable = config.NODE_FAILURE_POLICY == "retry" and retry_count < config.MAX_RETRY_COUNT
        for error_code, message in all_issues:
            errors.append(
                make_error(
                    node="verify",
                    error_code=error_code,
                    message=message,
                    retryable=retryable,
                )
            )

    return {
        "verification": report,
        "quiz_items": valid_quiz_items,
        "status": status,
        "errors": errors,
        "retry_count": retry_count + 1 if not passed else retry_count,
    }


def make_error(node: str, error_code: ErrorCode, message: str, retryable: bool) -> NodeError:
    """검증 이슈 하나를 NodeError 객체로 변환합니다.

    Args:
        node: 에러를 발생시킨 노드 이름 (예: "verify").
        error_code: schemas.errors.ErrorCode 에 정의된 에러 종류.
        message: 이슈를 설명하는 메시지.
        retryable: supervisor 가 재실행을 시도해도 되는지 여부.

    Returns:
        입력값으로 구성된 NodeError 인스턴스.
    """
    return NodeError(
        node=node,
        error_code=error_code,
        message=message,
        retryable=retryable,
    )
