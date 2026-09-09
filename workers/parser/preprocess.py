"""
B — 메타데이터 + 텍스트 정제 (공백/특수문자, LLM 컨텍스트용).

연동: pdf_parser.py, code_parser.py → nodes.py
"""

from __future__ import annotations

from schemas.files import Chunk, FileInfo


def extract_metadata(file: FileInfo) -> FileInfo:
    raise NotImplementedError("B: extract_metadata")


def refine_text(chunks: list[Chunk]) -> list[Chunk]:
    raise NotImplementedError("B: refine_text")
