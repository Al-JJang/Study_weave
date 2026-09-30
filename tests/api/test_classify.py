"""코드 폴더 경로 정리와 주제 휴리스틱."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from api.classify import FolderEntry, classify_folder, heuristic_topic, snippet_from_bytes
from api.paths import (
    is_code_folder_file,
    normalize_relpath,
    sanitize_relpath,
    should_skip_relpath,
    strip_root_segment,
)


def test_strip_root_and_skip_vendor_dirs() -> None:
    rel = strip_root_segment(normalize_relpath("week3/node_modules/pkg/index.js"))
    assert rel == "node_modules/pkg/index.js"
    assert should_skip_relpath(rel)
    assert not is_code_folder_file("week3/slide.pdf")
    assert is_code_folder_file("src/agent.py")


def test_sanitize_relpath_keeps_nested_code() -> None:
    assert sanitize_relpath("rag/hybrid.py") == "rag/hybrid.py"
    with pytest.raises(ValueError):
        sanitize_relpath("../secret.py")
    assert should_skip_relpath("node_modules/pkg/index.js")


def test_heuristic_reads_keywords() -> None:
    assert heuristic_topic("src/agent.py", "from langgraph.graph import StateGraph") == "LangGraph"
    assert heuristic_topic("rag/hybrid.py", "def retrieve():\n    return chunks") == "RAG"


def test_classify_forced_topic() -> None:
    entries = [
        FolderEntry(path="a.py", payload=b"print(1)\n", snippet="print(1)"),
        FolderEntry(path="b.py", payload=b"print(2)\n", snippet="print(2)"),
    ]
    mapping, how = classify_folder(entries, forced_topic="퀴즈")
    assert how == "topic"
    assert mapping == {"a.py": "퀴즈", "b.py": "퀴즈"}


def test_classify_falls_back_without_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("api.classify.config.GEMINI_API_KEY", None)
    entries = [
        FolderEntry(path="agent/loop.py", payload=b"print(1)\n", snippet="print(1)"),
        FolderEntry(path="rag/retriever.py", payload=b"return docs\n", snippet="return docs"),
    ]
    mapping, how = classify_folder(entries)
    assert how == "heuristic"
    assert mapping["agent/loop.py"] == "에이전트"
    assert mapping["rag/retriever.py"] == "RAG"


def test_classify_uses_gemini_json(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("api.classify.config.GEMINI_API_KEY", "test-key")

    class FakeModel:
        def invoke(self, _messages: object) -> SimpleNamespace:
            return SimpleNamespace(
                content='{"files":[{"path":"src/agent.py","topic":"LangGraph"}]}'
            )

    monkeypatch.setattr("api.classify.get_chat_model", lambda **_: FakeModel())
    entries = [FolderEntry(path="src/agent.py", payload=b"x=1\n", snippet="x=1")]
    mapping, how = classify_folder(entries)
    assert how == "gemini"
    assert mapping["src/agent.py"] == "LangGraph"


def test_snippet_skips_binary() -> None:
    assert snippet_from_bytes(b"\x00\x01\x02") == ""
    assert "hello" in snippet_from_bytes(b"hello\nworld")
