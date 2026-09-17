"""
A — LangGraph Supervisor.

흐름:
    START → route → parse → retrieve → analyze → format → verify → END
    retryable 이면 verify → analyze (add_conditional_edges)

연동:
    graph/router.py, graph/verify.py
    workers/parser/nodes.py, workers/analysis/nodes.py, workers/formatter/nodes.py
    schemas.state.AgentState, mocks.data, ui/app.py
"""

from __future__ import annotations

from typing import Literal

from langgraph.graph import END, START, StateGraph

import config
from graph.router import route_input_node
from mocks.data import (
    MOCK_CODE_UNITS,
    MOCK_CONCEPTS,
    MOCK_CROSS_REFERENCES,
    MOCK_FILES,
    MOCK_FLOWS,
    MOCK_MARKDOWN,
    MOCK_PARSED_CHUNKS,
    MOCK_PRACTICE_NOTES,
    MOCK_QUIZ_ITEMS,
    MOCK_REQUEST_ID,
    MOCK_RETRIEVED_CHUNKS,
    MOCK_TABLES,
)
from schemas.errors import VerificationReport
from schemas.files import FileInfo
from schemas.state import AgentState

USE_MOCK = True


def mock_parse_node(state: AgentState) -> dict:
    return {"parsed_chunks": MOCK_PARSED_CHUNKS, "files": MOCK_FILES, "status": "parsed"}


def mock_retrieve_node(state: AgentState) -> dict:
    return {"retrieved_chunks": MOCK_RETRIEVED_CHUNKS, "status": "retrieved"}


def mock_analyze_node(state: AgentState) -> dict:
    route = state.get("route", "both")
    payload: dict = {
        "status": "analyzed",
        "concepts": [],
        "code_units": [],
        "flows": [],
        "tables": [],
        "cross_references": [],
        "practice_notes": [],
    }
    if route in ("pdf_only", "both"):
        payload["concepts"] = MOCK_CONCEPTS
        payload["flows"] = MOCK_FLOWS
        payload["tables"] = MOCK_TABLES
    if route in ("code_only", "both"):
        payload["code_units"] = MOCK_CODE_UNITS
    if route == "both":
        payload["cross_references"] = MOCK_CROSS_REFERENCES
        payload["practice_notes"] = MOCK_PRACTICE_NOTES
    return payload


def mock_format_node(state: AgentState) -> dict:
    return {
        "quiz_items": MOCK_QUIZ_ITEMS,
        "final_markdown": MOCK_MARKDOWN,
        "status": "formatted",
    }


def mock_verify_node(state: AgentState) -> dict:
    report = VerificationReport(passed=True, issues=[], dropped_quiz_ids=[])
    return {"verification": report, "status": "completed"}


def route_after_verify(state: AgentState) -> Literal["analyze", "__end__"]:
    """verify 이후 재시도할지 끝낼지 결정한다.

    NodeError.retryable 은 생성 시점의 retry_count 로 고정되는 값이라 여러 번
    실패하며 errors 에 누적되면 stale 한 True 가 섞여 남는다. 그래서 개별
    에러가 아니라 최신 status/retry_count/policy 를 직접 본다.

    Args:
        state: verify_node 가 갱신한 AgentState. status, retry_count 를
            참조합니다.

    Returns:
        검증 실패 + retry 정책 + retry_count 가 한도 이내면 "analyze",
        아니면 "__end__".
    """
    if state.get("status") != "failed":
        return "__end__"
    if config.NODE_FAILURE_POLICY != "retry":
        return "__end__"
    if state.get("retry_count", 0) > config.MAX_RETRY_COUNT:
        return "__end__"
    return "analyze"


def build_graph(*, use_mock: bool = USE_MOCK):
    if use_mock:
        parse_node = mock_parse_node
        retrieve_node = mock_retrieve_node
        analyze_node = mock_analyze_node
        format_node = mock_format_node
        verify_node = mock_verify_node
    else:
        from graph.verify import verify_node as real_verify_node
        from workers.analysis.nodes import analyze_node as real_analyze_node
        from workers.formatter.nodes import format_node as real_format_node
        from workers.parser.nodes import parse_files_node, retrieve_chunks_node

        parse_node = parse_files_node
        retrieve_node = retrieve_chunks_node
        analyze_node = real_analyze_node
        format_node = real_format_node
        verify_node = real_verify_node

    builder = StateGraph(AgentState)
    builder.add_node("route", route_input_node)
    builder.add_node("parse", parse_node)
    builder.add_node("retrieve", retrieve_node)
    builder.add_node("analyze", analyze_node)
    builder.add_node("format", format_node)
    builder.add_node("verify", verify_node)

    builder.add_edge(START, "route")
    builder.add_edge("route", "parse")
    builder.add_edge("parse", "retrieve")
    builder.add_edge("retrieve", "analyze")
    builder.add_edge("analyze", "format")
    builder.add_edge("format", "verify")
    builder.add_conditional_edges(
        "verify", route_after_verify, {"analyze": "analyze", "__end__": END}
    )
    return builder.compile()


def run_pipeline(files: list[FileInfo] | None = None, *, use_mock: bool = USE_MOCK) -> AgentState:
    graph = build_graph(use_mock=use_mock)
    initial: AgentState = {
        "request_id": MOCK_REQUEST_ID,
        "files": files or MOCK_FILES,
        "parsed_chunks": [],
        "retrieved_chunks": [],
        "concepts": [],
        "code_units": [],
        "flows": [],
        "tables": [],
        "cross_references": [],
        "practice_notes": [],
        "quiz_items": [],
        "final_markdown": None,
        "errors": [],
        "retry_count": 0,
    }
    return graph.invoke(initial)


if __name__ == "__main__":
    result = run_pipeline()
    print("=" * 70)
    print("StudyWave mock graph")
    print("=" * 70)
    print("route :", result.get("route"))
    print("status:", result.get("status"))
    print("chunks:", len(result.get("parsed_chunks", [])))
    print("hits  :", len(result.get("retrieved_chunks", [])))
    print("quiz  :", len(result.get("quiz_items", [])))
    print("passed:", getattr(result.get("verification"), "passed", None))
