"""verify → analyze 재시도 conditional edge 동작 확인."""

from __future__ import annotations

import config
from graph.supervisor import route_after_verify
from graph.verify import verify_node
from schemas.quiz import QuizItem


def _bad_state(retry_count: int) -> dict:
    bad_item = QuizItem(
        quiz_type="mcq",
        question="q",
        options=["A", "B"],
        answer="A",
        explanation="e",
        source_chunk_ids=["missing_chunk"],
    )
    return {"quiz_items": [bad_item], "route": "both", "retry_count": retry_count, "errors": []}


def test_route_after_verify_ends_when_passed():
    assert route_after_verify({"status": "completed", "retry_count": 0}) == "__end__"


def test_route_after_verify_ends_when_policy_not_retry(monkeypatch):
    monkeypatch.setattr(config, "NODE_FAILURE_POLICY", "partial")
    assert route_after_verify({"status": "failed", "retry_count": 0}) == "__end__"


def test_route_after_verify_retries_then_stops_at_max(monkeypatch):
    """MAX_RETRY_COUNT 넘으면 반드시 멈춘다 (누적 errors 의 stale retryable 에 안 낚임)."""
    monkeypatch.setattr(config, "NODE_FAILURE_POLICY", "retry")
    monkeypatch.setattr(config, "MAX_RETRY_COUNT", 2)

    state = _bad_state(retry_count=0)
    decisions = []
    for _ in range(5):  # 넉넉히 돌려서 무한루프면 여기서 확실히 드러남
        result = verify_node(state)
        decision = route_after_verify(result)
        decisions.append(decision)
        if decision == "__end__":
            break
        state = {**state, "retry_count": result["retry_count"], "errors": result["errors"]}

    assert decisions == ["analyze", "analyze", "__end__"]
