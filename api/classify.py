"""강사 코드 폴더를 주제별로 나눈다. Gemini가 있으면 쓰고, 없으면 경로 휴리스틱."""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass
from typing import Any, Literal

from langchain_core.messages import HumanMessage, SystemMessage

import config
from api.paths import normalize_topic
from config import get_chat_model

logger = logging.getLogger(__name__)

ClassifiedBy = Literal["gemini", "heuristic", "topic"]

MAX_FILES = 80
MAX_FOLDER_BYTES = 40 * 1024 * 1024
MAX_FILE_BYTES = 2 * 1024 * 1024
MAX_SNIPPET_CHARS = 700
MAX_PROMPT_CHARS = 18_000

_KEYWORD_TOPICS = (
    ("langgraph", "LangGraph"),
    ("langchain", "LangChain"),
    ("hybridrag", "RAG"),
    ("hybrid_rag", "RAG"),
    ("retriev", "RAG"),
    ("vector", "RAG"),
    ("embedding", "RAG"),
    ("rag", "RAG"),
    ("agent", "에이전트"),
    ("tool", "에이전트"),
    ("quiz", "퀴즈"),
    ("streamlit", "Streamlit"),
    ("fastapi", "FastAPI"),
    ("prompt", "프롬프트"),
)

_GENERIC_DIRS = frozenset(
    {"src", "lib", "app", "code", "codes", "files", "examples", "example", "demo", "tmp", "temp"}
)


@dataclass(frozen=True)
class FolderEntry:
    path: str
    payload: bytes
    snippet: str


def snippet_from_bytes(payload: bytes, *, limit: int = MAX_SNIPPET_CHARS) -> str:
    if not payload:
        return ""
    sample = payload[: min(len(payload), 8_000)]
    if b"\x00" in sample[:1024]:
        return ""
    text = sample.decode("utf-8", errors="replace").replace("\x00", "")
    return text[:limit]


def _message_text(content: object) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict) and isinstance(item.get("text"), str):
                parts.append(item["text"])
        return "".join(parts)
    return str(content) if content else ""


def _extract_json_object(raw: str) -> dict[str, Any]:
    text = raw.strip()
    fenced = re.search(r"```(?:json)?\s*(\{.*\})\s*```", text, re.DOTALL)
    if fenced:
        text = fenced.group(1)
    else:
        start = text.find("{")
        end = text.rfind("}")
        if start >= 0 and end > start:
            text = text[start : end + 1]
    payload = json.loads(text)
    if not isinstance(payload, dict):
        raise ValueError("JSON 객체가 아닙니다.")
    return payload


def heuristic_topic(path: str, snippet: str = "") -> str:
    hay = f"{path}\n{snippet}".lower()
    for needle, topic in _KEYWORD_TOPICS:
        if needle in hay:
            return topic
    parts = [
        part
        for part in path.replace("\\", "/").split("/")
        if part and part.lower() not in _GENERIC_DIRS
    ]
    if len(parts) >= 2:
        return normalize_topic(parts[0])
    return "미분류"


def heuristic_topics(entries: list[FolderEntry]) -> dict[str, str]:
    return {item.path: heuristic_topic(item.path, item.snippet) for item in entries}


def _gemini_topics(entries: list[FolderEntry], *, known_topics: list[str]) -> dict[str, str]:
    known = ", ".join(known_topics) if known_topics else "없음"
    blocks: list[str] = []
    used = 0
    for item in entries:
        block = f"PATH: {item.path}\n{item.snippet}\n"
        if used + len(block) > MAX_PROMPT_CHARS:
            blocks.append(f"PATH: {item.path}\n")
            continue
        blocks.append(block)
        used += len(block)
    prompt = (
        "아래는 강사님이 폴더째 올린 수업 코드다. 각 파일을 수업 주제로 나눠라.\n"
        f"이미 있는 주제: {known}\n"
        "가능하면 기존 주제를 그대로 쓰고, 새로 만들 때는 짧은 한글/영문 이름(40자 이내)을 쓴다.\n"
        "같은 예제·프로젝트는 같은 주제. skip은 false로 둔다.\n"
        'JSON만 출력: {"files":[{"path":"상대경로","topic":"주제"}]}\n\n' + "\n---\n".join(blocks)
    )
    model = get_chat_model(role="generate")
    response = model.invoke(
        [
            SystemMessage(content="너는 StudyWeave 코드 분류기다. JSON만 출력한다."),
            HumanMessage(content=prompt),
        ]
    )
    payload = _extract_json_object(_message_text(getattr(response, "content", "")))
    rows = payload.get("files")
    if not isinstance(rows, list):
        raise ValueError("files 배열이 없습니다.")
    mapping: dict[str, str] = {}
    by_path = {item.path: item for item in entries}
    for row in rows:
        if not isinstance(row, dict):
            continue
        path = str(row.get("path") or "").strip()
        if path not in by_path:
            continue
        mapping[path] = normalize_topic(str(row.get("topic") or ""))
    if not mapping:
        raise ValueError("분류 결과가 비었습니다.")
    for item in entries:
        mapping.setdefault(item.path, heuristic_topic(item.path, item.snippet))
    return mapping


def classify_folder(
    entries: list[FolderEntry],
    *,
    forced_topic: str | None = None,
    known_topics: list[str] | None = None,
) -> tuple[dict[str, str], ClassifiedBy]:
    if forced_topic and forced_topic.strip() and normalize_topic(forced_topic) != "미분류":
        topic = normalize_topic(forced_topic)
        return {item.path: topic for item in entries}, "topic"
    if config.GEMINI_API_KEY:
        try:
            return _gemini_topics(entries, known_topics=known_topics or []), "gemini"
        except Exception:
            logger.exception("코드 폴더 Gemini 분류 실패 — 휴리스틱으로 대체")
    return heuristic_topics(entries), "heuristic"
