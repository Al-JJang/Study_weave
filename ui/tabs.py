"""
Streamlit 탭.

합의 탭: [개념 요약] [코드 흐름 분석] [복습 퀴즈]
퀴즈 정답/해설은 toggle/accordion.
마크다운 다운로드는 Obsidian YAML.

연동: graph.supervisor.run_pipeline 결과 AgentState
"""

from __future__ import annotations

from schemas.state import AgentState


def render_concept_tab(state: AgentState) -> None:
    raise NotImplementedError("UI: render_concept_tab")


def render_code_tab(state: AgentState) -> None:
    raise NotImplementedError("UI: render_code_tab")


def render_quiz_tab(state: AgentState) -> None:
    raise NotImplementedError("UI: render_quiz_tab")
