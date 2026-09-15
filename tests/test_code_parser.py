from __future__ import annotations

from pathlib import Path

import pytest

from schemas.files import FileInfo
from workers.parser.code_parser import (
    FALLBACK_STRIDE_LINES,
    FALLBACK_WINDOW_LINES,
    parse_code,
)

SIMPLE_MODULE = """import os

VERSION = "1.0"


def load(path):
    return os.path.exists(path)


async def fetch(url):
    return url
"""

CLASS_MODULE = '''class Store:
    """저장소."""

    def put(self, key):
        return key

    def get(self, key):
        return key


def helper():
    return Store()
'''

DECORATED_MODULE = """import functools


@functools.cache
def cached():
    return 1
"""

NESTED_MODULE = """def outer():
    def inner():
        return 2

    return inner()
"""


def _write_module(path: Path, source: str) -> FileInfo:
    path.write_text(source, encoding="utf-8")
    return FileInfo(
        document_id=f"req-demo-001:{path.name}",
        filename=path.name,
        source_type="code",
        path=str(path),
    )


def test_parse_code_splits_module_level_definitions(tmp_path: Path) -> None:
    file = _write_module(tmp_path / "loader.py", SIMPLE_MODULE)

    chunks = parse_code(file)

    assert [(chunk.start_line, chunk.end_line) for chunk in chunks] == [(1, 3), (6, 7), (10, 11)]
    assert chunks[0].content == 'import os\n\nVERSION = "1.0"'
    assert chunks[1].content == "def load(path):\n    return os.path.exists(path)"
    assert chunks[2].content.startswith("async def fetch(url):")


def test_parse_code_fills_chunk_contract(tmp_path: Path) -> None:
    file = _write_module(tmp_path / "loader.py", SIMPLE_MODULE)

    chunks = parse_code(file)

    assert chunks[0].chunk_id == "req-demo-001:loader.py:chunk:0000"
    assert chunks[1].chunk_id == "req-demo-001:loader.py:chunk:0001"
    assert [chunk.chunk_index for chunk in chunks] == [0, 1, 2]
    for chunk in chunks:
        assert chunk.document_id == "req-demo-001:loader.py"
        assert chunk.source_type == "code"
        assert chunk.page_number is None
        assert chunk.start_line is not None and chunk.end_line is not None


def test_parse_code_keeps_class_whole_without_duplicating_methods(tmp_path: Path) -> None:
    file = _write_module(tmp_path / "store.py", CLASS_MODULE)

    chunks = parse_code(file)

    assert [(chunk.start_line, chunk.end_line) for chunk in chunks] == [(1, 8), (11, 12)]
    assert chunks[0].content.startswith("class Store:")
    assert "def put(self, key):" in chunks[0].content
    assert "def get(self, key):" in chunks[0].content
    assert sum("def put(self, key):" in chunk.content for chunk in chunks) == 1


def test_parse_code_starts_at_decorator_line(tmp_path: Path) -> None:
    file = _write_module(tmp_path / "cache.py", DECORATED_MODULE)

    chunks = parse_code(file)

    assert (chunks[-1].start_line, chunks[-1].end_line) == (4, 6)
    assert chunks[-1].content.startswith("@functools.cache\n")


def test_parse_code_keeps_nested_function_inside_parent(tmp_path: Path) -> None:
    file = _write_module(tmp_path / "nested.py", NESTED_MODULE)

    chunks = parse_code(file)

    assert len(chunks) == 1
    assert (chunks[0].start_line, chunks[0].end_line) == (1, 5)
    assert "def inner():" in chunks[0].content


def test_parse_code_preserves_indentation(tmp_path: Path) -> None:
    file = _write_module(tmp_path / "nested.py", NESTED_MODULE)

    chunks = parse_code(file)

    assert "    def inner():" in chunks[0].content
    assert "        return 2" in chunks[0].content


def test_parse_code_returns_empty_for_blank_file(tmp_path: Path) -> None:
    assert parse_code(_write_module(tmp_path / "empty.py", "")) == []
    assert parse_code(_write_module(tmp_path / "blank.py", "\n\n   \n")) == []


def test_parse_code_falls_back_to_window_on_syntax_error(tmp_path: Path) -> None:
    broken = "\n".join([f"value_{index} = {index}" for index in range(120)] + ["def (:"])
    file = _write_module(tmp_path / "broken.py", broken)

    chunks = parse_code(file)

    total_lines = 121
    assert chunks[0].start_line == 1
    assert chunks[0].end_line == FALLBACK_WINDOW_LINES
    assert chunks[1].start_line == 1 + FALLBACK_STRIDE_LINES
    assert chunks[-1].end_line == total_lines
    assert len(chunks) > 1
    assert "value_0 = 0" in chunks[0].content


def test_parse_code_last_chunk_reaches_end_of_file(tmp_path: Path) -> None:
    source = "def only():\n    return 1"
    file = _write_module(tmp_path / "tail.py", source)

    chunks = parse_code(file)

    assert (chunks[-1].start_line, chunks[-1].end_line) == (1, 2)
    assert chunks[-1].content == source


def test_parse_code_raises_when_file_missing(tmp_path: Path) -> None:
    file = FileInfo(
        document_id="req-demo-001:missing.py",
        filename="missing.py",
        source_type="code",
        path=str(tmp_path / "missing.py"),
    )

    with pytest.raises(FileNotFoundError):
        parse_code(file)
