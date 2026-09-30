"""대시보드 챗봇. Gemini는 config.get_chat_model 을 그대로 쓴다."""

from __future__ import annotations

import json
from collections.abc import Iterator
from typing import Any

from fastapi import HTTPException
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

import api.store as store
import config
from api.models import ChatRequest
from api.users import require_user_id
from config import get_chat_model

MISSING_KEY_DETAIL = (
    "GEMINI_API_KEY가 없습니다. 프로젝트 루트 .env에 GEMINI_API_KEY를 넣고 서버를 다시 시작하세요."
)
MAX_NOTES = 5
MAX_NOTE_CHARS = 2500
MAX_CONTEXT_CHARS = 12_000


def _chunk_text(chunk: object) -> str:
    content = getattr(chunk, "content", "")
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


def _note_context(user_id: str) -> str:
    notes = store.list_notes(user_id=user_id)[:MAX_NOTES]
    if not notes:
        return "아직 이 사용자의 노트가 없습니다."
    blocks: list[str] = []
    used = 0
    for note in notes:
        body = note.markdown[:MAX_NOTE_CHARS]
        block = f"## {note.title}\n{body}"
        if used + len(block) > MAX_CONTEXT_CHARS:
            break
        blocks.append(block)
        used += len(block)
    return "\n\n".join(blocks) if blocks else "아직 이 사용자의 노트가 없습니다."


def _messages(body: ChatRequest, user_id: str) -> list[SystemMessage | HumanMessage | AIMessage]:
    context = _note_context(user_id)
    system = (
        "너는 StudyWeave AI의 학습 도우미다. 아래는 선택한 팀원의 최근 노트다. "
        "노트 내용에 근거해 한국어로 짧게 답한다. 노트에 없으면 없다고 말한다.\n\n"
        f"{context}"
    )
    messages: list[SystemMessage | HumanMessage | AIMessage] = [SystemMessage(content=system)]
    for turn in body.history[-12:]:
        if turn.role == "assistant":
            messages.append(AIMessage(content=turn.content))
        else:
            messages.append(HumanMessage(content=turn.content))
    messages.append(HumanMessage(content=body.message.strip()))
    return messages


def prepare_chat(body: ChatRequest) -> tuple[Any, str]:
    """키·사용자·질문을 먼저 검사하고 모델을 연다. 실패는 HTTPException."""
    user_id = require_user_id(body.user_id)
    if not body.message.strip():
        raise HTTPException(status_code=400, detail="질문을 입력하세요.")
    if not config.GEMINI_API_KEY:
        raise HTTPException(status_code=503, detail=MISSING_KEY_DETAIL)
    try:
        model = get_chat_model(role="generate")
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except NotImplementedError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return model, user_id


def iter_chat_sse(model: Any, body: ChatRequest, user_id: str) -> Iterator[str]:
    try:
        for chunk in model.stream(_messages(body, user_id)):
            text = _chunk_text(chunk)
            if text:
                yield f"data: {json.dumps({'delta': text}, ensure_ascii=False)}\n\n"
        yield "data: [DONE]\n\n"
    except Exception as exc:
        yield f"data: {json.dumps({'error': str(exc)}, ensure_ascii=False)}\n\n"
