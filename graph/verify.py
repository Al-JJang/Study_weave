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

from schemas.errors import NodeError
from schemas.quiz import QuizItem
from schemas.state import AgentState


def collect_known_chunk_ids(state: AgentState) -> set[str]:
    raise NotImplementedError("A: collect_known_chunk_ids")


def validate_citations(state: AgentState) -> list[str]:
    raise NotImplementedError("A: validate_citations")


def validate_quiz_items(items: list[QuizItem]) -> tuple[list[QuizItem], list[int], list[str]]:
    raise NotImplementedError("A: validate_quiz_items")


def validate_route_outputs(state: AgentState) -> list[str]:
    raise NotImplementedError("A: validate_route_outputs")


def verify_node(state: AgentState) -> dict:
    """반환 key: verification, quiz_items, status, errors."""
    raise NotImplementedError("A: verify_node")


def make_error(node: str, error_code: str, message: str, retryable: bool) -> NodeError:
    return NodeError(
        node=node,
        error_code=error_code,
        message=message,
        retryable=retryable,
    )
