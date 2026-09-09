"""
C 계약 — 개념 / 코드흐름 / 이론-코드 연결 / Troubleshooting.

연동:
    씀 ← workers/analysis/*
    읽힘 → workers/formatter/quiz.py, workers/formatter/markdown.py, graph/verify.py, ui/tabs.py
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class ConceptItem(BaseModel):
    title: str
    summary: str
    source_chunk_ids: list[str] = Field(min_length=1)


class CodeAnalysisItem(BaseModel):
    title: str
    explanation: str
    source_chunk_ids: list[str] = Field(min_length=1)


class CrossReferenceItem(BaseModel):
    theory_chunk_ids: list[str]
    code_chunk_ids: list[str]
    explanation: str


class TroubleshootingItem(BaseModel):
    symptom: str
    cause: str
    fix: str
    source_chunk_ids: list[str] = Field(default_factory=list)


class AnalysisLLMOutput(BaseModel):
    """C structured output. 강의 GraphQueryPlan.model_json_schema() 자리."""

    concept_summary: list[ConceptItem] = Field(default_factory=list)
    code_analysis: list[CodeAnalysisItem] = Field(default_factory=list)
    cross_references: list[CrossReferenceItem] = Field(default_factory=list)
    troubleshooting: list[TroubleshootingItem] = Field(default_factory=list)
