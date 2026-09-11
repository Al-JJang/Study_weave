"""ChromaDB 제거 이후 config 모듈이 pgvector 단일 백엔드 상태를 유지하는지 확인."""

from __future__ import annotations

import config


def test_chroma_settings_removed():
    assert not hasattr(config, "CHROMA_DIR")
    assert not hasattr(config, "VECTOR_BACKEND")


def test_database_url_defaults_to_postgres():
    assert config.DATABASE_URL.startswith("postgresql://")
