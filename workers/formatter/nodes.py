"""
D — Graph Node (format).

반환 key: quiz_items, final_markdown, status

연동: quiz.py, markdown.py, graph/supervisor.py
"""

from __future__ import annotations

from schemas.state import AgentState


def format_node(state: AgentState) -> dict:
    raise NotImplementedError("D: format_node")
