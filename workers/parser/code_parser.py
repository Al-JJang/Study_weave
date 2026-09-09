"""
B — 코드 파서.

합의: ast 또는 정규식으로 함수/클래스/주석 단위 분할.
연동: preprocess.py → nodes.py
"""

from __future__ import annotations

from schemas.files import Chunk, FileInfo


def parse_code(file: FileInfo) -> list[Chunk]:
    raise NotImplementedError("B: parse_code — ast / regex")
