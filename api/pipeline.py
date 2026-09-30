"""그래프 호출은 여기서만. 워커/그래프 파일을 수정하지 않는다."""

from __future__ import annotations

import importlib
import logging

logger = logging.getLogger(__name__)


def graph_available() -> bool:
    try:
        importlib.import_module("graph.supervisor")
    except Exception:
        return False
    return True


def try_mock_markdown() -> str | None:
    """그래프가 있으면 mock 파이프라인 결과를 쓰고, 없으면 None.

    `USE_MOCK=True` 인 현재 main에서는 업로드 파일 내용과 무관한
    샘플 마크다운이 돌아온다. UI 뼈대가 비지 않게 하려는 용도다.
    """
    try:
        from graph.supervisor import run_pipeline

        result = run_pipeline(use_mock=True)
        markdown = result.get("final_markdown")
        if isinstance(markdown, str) and markdown.strip():
            return markdown
    except Exception:
        logger.exception("mock 파이프라인 호출 실패 — placeholder 노트로 대체")
    return None
