"""
D — Obsidian/Notion 호환 마크다운.

목차: YAML → 개념 → 코드 → 이론-코드 연결 → Troubleshooting → Quiz
토글/콜아웃: <details>, > [!NOTE]
빈 섹션: config.EMPTY_SECTION_POLICY

연동: C 산출 + quiz.py → final_markdown → ui/tabs.py (다운로드)
"""

from __future__ import annotations

from schemas.state import AgentState


def format_markdown(state: AgentState) -> str:
    raise NotImplementedError("D: format_markdown")
