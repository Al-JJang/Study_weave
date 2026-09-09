"""
D — 복습 퀴즈 3~5문항 (주관/객관) + 해설.

연동: schemas.quiz.QuizItem, workers/analysis 산출, graph/supervisor.py, markdown.py
LLM: config.get_chat_model(role="generate") 기본 Gemini Tier 3
"""

from __future__ import annotations

from schemas.quiz import QuizItem
from schemas.state import AgentState


def produce_quiz_items(state: AgentState) -> list[QuizItem]:
    raise NotImplementedError("D: produce_quiz_items")
