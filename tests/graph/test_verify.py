"""verify_node 핵심 검증 로직(citation/quiz/route) 확인."""

from __future__ import annotations

from types import SimpleNamespace

import config
from graph.verify import validate_quiz_items, validate_route_outputs, verify_node
from mocks.data import (
    MOCK_CODE_UNITS,
    MOCK_CONCEPTS,
    MOCK_CROSS_REFERENCES,
    MOCK_PARSED_CHUNKS,
    MOCK_QUIZ_ITEMS,
)


def _clean_state(**overrides) -> dict:
    state = {
        "parsed_chunks": MOCK_PARSED_CHUNKS,
        "retrieved_chunks": [],
        "concepts": MOCK_CONCEPTS,
        "code_units": MOCK_CODE_UNITS,
        "cross_references": MOCK_CROSS_REFERENCES,
        "quiz_items": MOCK_QUIZ_ITEMS,
        "route": "both",
        "retry_count": 0,
        "errors": [],
    }
    state.update(overrides)
    return state


def test_verify_node_passes_on_clean_mock_state():
    """mocks/data 그대로 넣으면 통과해야 한다 (false-positive 실패 방지)."""
    result = verify_node(_clean_state())
    assert result["status"] == "completed"
    assert result["verification"].passed is True
    assert result["retry_count"] == 0
    assert result["quiz_items"] == MOCK_QUIZ_ITEMS


def test_validate_route_outputs_flags_missing_required_section():
    assert validate_route_outputs({"route": "pdf_only", "concepts": []})
    assert validate_route_outputs({"route": "code_only", "code_units": []})
    assert validate_route_outputs({"route": "both", "cross_references": []})
    assert not validate_route_outputs({"route": "pdf_only", "concepts": MOCK_CONCEPTS})


def test_validate_quiz_items_drops_mismatched_answer_but_keeps_valid():
    # QuizItem 자체 pydantic validator가 mcq answer∉options를 생성 시점에 막기 때문에
    # 실제 QuizItem으로는 이 분기를 못 만듦 -> duck-typed 가짜 객체로 직접 검사.
    bad = SimpleNamespace(quiz_type="mcq", answer="C", options=["A", "B"])
    good = SimpleNamespace(quiz_type="short", answer="ans", options=[])

    valid_items, dropped_quiz_ids, issues = validate_quiz_items([bad, good])

    assert valid_items == [good]
    assert dropped_quiz_ids == [0]
    assert issues and issues[0][0] == "QUIZ_ANSWER_MISMATCH"


def test_verify_node_default_policy_is_not_retryable(monkeypatch):
    monkeypatch.setattr(config, "NODE_FAILURE_POLICY", "partial")
    state = _clean_state(cross_references=[])  # both route인데 비움 -> EMPTY_SECTION

    result = verify_node(state)

    assert result["status"] == "failed"
    assert result["errors"] and all(not e.retryable for e in result["errors"])
