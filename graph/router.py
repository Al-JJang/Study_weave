"""
A — 입력 조합 라우터.

연동:
    import ← schemas.files.FileInfo, schemas.state.AgentState
    불림 → graph/supervisor.py (node "route")
"""

from __future__ import annotations

from typing import Literal

from schemas.files import FileInfo
from schemas.state import AgentState


def detect_route(files: list[FileInfo]) -> Literal["pdf_only", "code_only", "both"]:
    types = {file.source_type for file in files}
    if types == {"pdf"}:
        return "pdf_only"
    if types == {"code"}:
        return "code_only"
    return "both"


def route_input_node(state: AgentState) -> dict:
    route = detect_route(state.get("files", []))
    return {
        "route": route,
        "status": "received",
        "parsed_chunks": state.get("parsed_chunks", []),
        "retrieved_chunks": state.get("retrieved_chunks", []),
        "errors": state.get("errors", []),
        "retry_count": state.get("retry_count", 0),
    }
