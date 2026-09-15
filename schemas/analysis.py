"""
C 계약 — 개념 / 코드 단위 / 흐름도 / 참조표 / 교차매핑 / 실무 노트.

연동:
    씀 ← workers/analysis/*
    읽힘 → workers/formatter/quiz.py, workers/formatter/markdown.py, graph/verify.py, ui/tabs.py
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class ConceptItem(BaseModel):
    concept_id: str
    title: str
    summary: str
    formula: str | None = None  # LaTeX 또는 읽을 수 있는 일반식. content_type="formula" 청크 근거
    needs_verification: bool = False  # 근거 청크에 extraction_method="vision"이 섞여 있으면 True
    related_code_refs: list[str] = Field(default_factory=list)
    source_chunk_ids: list[str]


class CodeAnalysisItem(BaseModel):
    unit_name: str
    unit_type: Literal["function", "file", "layer"]
    execution_flow: str
    key_points: list[str] = Field(default_factory=list)
    source_chunk_ids: list[str] = Field(min_length=1)


class FlowDiagram(BaseModel):
    scope: Literal["pipeline", "curriculum_progression", "execution_trace"]
    title: str
    diagram: str
    description: str
    needs_verification: bool = False  # content_type="diagram" 청크가 vision 추출인 경우 True
    source_chunk_ids: list[str]


class ReferenceTable(BaseModel):
    title: str
    columns: list[str]
    rows: list[list[str]]
    source_chunk_ids: list[str]


class CrossReferenceItem(BaseModel):
    ref_type: Literal["matched", "code_only", "concept_only"]
    code_ref: str | None = None
    concept_ref: str | None = None
    explanation: str
    source_chunk_ids: list[str]


class PracticeNote(BaseModel):
    note_type: Literal["mistake", "tip", "checklist_item"]
    scope: Literal["learner_pattern", "source_code_defect"] = "learner_pattern"
    content: str
    caution: str | None = None
    source_chunk_ids: list[str]


class AnalysisOutput(BaseModel):
    """C 노드의 최종 반환값. AgentState의 대응 키에 그대로 매핑됨."""

    concepts: list[ConceptItem] = Field(default_factory=list)
    code_units: list[CodeAnalysisItem] = Field(default_factory=list)
    flows: list[FlowDiagram] = Field(default_factory=list)
    tables: list[ReferenceTable] = Field(default_factory=list)
    cross_references: list[CrossReferenceItem] = Field(default_factory=list)
    practice_notes: list[PracticeNote] = Field(default_factory=list)
