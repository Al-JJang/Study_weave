"""verify → analyze 재시도 conditional edge / mock analyze 노드의 route 분기 확인."""

from __future__ import annotations

import pytest

import config
from graph.supervisor import mock_analyze_node, route_after_verify
from graph.verify import verify_node
from schemas.quiz import QuizItem


@pytest.mark.parametrize("route", ["pdf_only", "code_only", "both"])
def test_mock_analyze_node_fills_flows_and_tables_for_every_route(route):
    """flows/tables 는 PDF·코드 양쪽에서 나오므로 실제 analyze_node 와 같이 route 를 가리지 않는다."""
    payload = mock_analyze_node({"route": route})
    assert payload["flows"]
    assert payload["tables"]


def test_mock_analyze_node_keeps_route_specific_sections_empty():
    pdf_only = mock_analyze_node({"route": "pdf_only"})
    assert pdf_only["code_units"] == []
    assert pdf_only["cross_references"] == []
    assert pdf_only["practice_notes"] == []

    code_only = mock_analyze_node({"route": "code_only"})
    assert code_only["concepts"] == []
    assert code_only["cross_references"] == []
    assert code_only["practice_notes"] == []


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
