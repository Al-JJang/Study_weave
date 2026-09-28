"""C analyze 노드 — 근거 직렬화 / chunk_id 검증 / route 분기. LLM 은 호출하지 않는다."""

from __future__ import annotations

from langchain_core.runnables import RunnableLambda

import config
from schemas.analysis import CodeAnalysisItem, ConceptItem
from schemas.files import RetrievedChunk
from workers.analysis.code_flow import CodeUnitList, produce_code_units
from workers.analysis.concept import ConceptList, produce_concepts
from workers.analysis.nodes import analyze_node, build_evidence_context


class _FakeModel:
    """with_structured_output 결과가 고정 payload 를 돌려주는 가짜 모델."""

    def __init__(self, payload):
        self._payload = payload

    def with_structured_output(self, schema):
        return RunnableLambda(lambda _: self._payload)


def _pdf_chunk(chunk_id: str, page_number: int = 1) -> RetrievedChunk:
    return RetrievedChunk(
        chunk_id=chunk_id,
        document_id="doc",
        source_type="pdf",
        content="이론 본문",
        chunk_index=0,
        page_number=page_number,
    )


def _code_chunk(chunk_id: str) -> RetrievedChunk:
    return RetrievedChunk(
        chunk_id=chunk_id,
        document_id="doc",
        source_type="code",
        content="def f(): ...",
        chunk_index=0,
        start_line=1,
        end_line=8,
    )


def test_build_evidence_context_labels_pdf_with_page():
    result = build_evidence_context([_pdf_chunk("c1", page_number=7)])
    assert result.startswith("[c1 | page:7]")
    assert "이론 본문" in result


def test_build_evidence_context_labels_code_with_line_range():
    result = build_evidence_context([_code_chunk("c2")])
    assert result.startswith("[c2 | line:1-8]")


def test_produce_concepts_skips_llm_without_pdf_chunks(monkeypatch):
    """PDF 청크가 없으면 API 를 부르지 않고 빈 리스트를 돌려준다."""

    def _boom(**_):
        raise AssertionError("LLM 을 호출하면 안 된다")

    monkeypatch.setattr(config, "get_chat_model", _boom)
    assert produce_concepts([_code_chunk("c1")]) == []


def test_produce_concepts_drops_unknown_chunk_ids(monkeypatch):
    """LLM 이 지어낸 chunk_id 를 인용한 항목은 근거가 없으므로 버린다."""
    chunk = _pdf_chunk("real")
    payload = ConceptList(
        concepts=[
            ConceptItem(
                concept_id="concept-001", title="유효", summary="s", source_chunk_ids=["real"]
            ),
            ConceptItem(
                concept_id="concept-002", title="환각", summary="s", source_chunk_ids=["made-up"]
            ),
        ]
    )
    monkeypatch.setattr(config, "get_chat_model", lambda **_: _FakeModel(payload))

    assert [item.concept_id for item in produce_concepts([chunk])] == ["concept-001"]


def test_produce_code_units_drops_unknown_chunk_ids(monkeypatch):
    chunk = _code_chunk("real")
    payload = CodeUnitList(
        code_units=[
            CodeAnalysisItem(
                unit_name="ok", unit_type="file", execution_flow="f", source_chunk_ids=["real"]
            ),
            CodeAnalysisItem(
                unit_name="hallucinated",
                unit_type="file",
                execution_flow="f",
                source_chunk_ids=["made-up"],
            ),
        ]
    )
    monkeypatch.setattr(config, "get_chat_model", lambda **_: _FakeModel(payload))

    assert [item.unit_name for item in produce_code_units([chunk])] == ["ok"]


def _stub_producers(monkeypatch) -> list[str]:
    """analyze_node 가 실제로 부른 producer 이름을 기록한다."""
    called: list[str] = []

    def _record(name, result):
        def _inner(*_args):
            called.append(name)
            return result

        return _inner

    monkeypatch.setattr("workers.analysis.nodes.produce_concepts", _record("concepts", []))
    monkeypatch.setattr("workers.analysis.nodes.produce_code_units", _record("code_units", []))
    monkeypatch.setattr(
        "workers.analysis.nodes.produce_cross_references", _record("cross_references", [])
    )
    return called


def test_analyze_node_pdf_only_runs_concepts_only(monkeypatch):
    called = _stub_producers(monkeypatch)
    analyze_node({"route": "pdf_only", "retrieved_chunks": []})
    assert called == ["concepts"]


def test_analyze_node_code_only_runs_code_units_only(monkeypatch):
    called = _stub_producers(monkeypatch)
    analyze_node({"route": "code_only", "retrieved_chunks": []})
    assert called == ["code_units"]


def test_analyze_node_both_runs_all_three(monkeypatch):
    called = _stub_producers(monkeypatch)
    analyze_node({"route": "both", "retrieved_chunks": []})
    assert called == ["concepts", "code_units", "cross_references"]


def test_analyze_node_always_returns_every_analysis_key(monkeypatch):
    """AgentState 규칙: 빈 결과라도 key 를 생략하지 않는다."""
    _stub_producers(monkeypatch)
    result = analyze_node({"route": "pdf_only", "retrieved_chunks": []})
    assert set(result) == {
        "status",
        "concepts",
        "code_units",
        "flows",
        "tables",
        "cross_references",
        "practice_notes",
    }
    assert result["status"] == "analyzed"
