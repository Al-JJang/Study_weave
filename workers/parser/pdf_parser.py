"""
B — PDF 파서.

합의: pypdf / pdfplumber 로 본문, 목차, 코드 블록 추출.
연동: preprocess.py → nodes.py → store/vector_store.py
"""

from __future__ import annotations

from schemas.files import Chunk, FileInfo


def parse_pdf(file: FileInfo) -> list[Chunk]:
    raise NotImplementedError("B: parse_pdf — pypdf / pdfplumber")
