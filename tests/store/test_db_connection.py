"""pgvector 로컬 DB 실제 연결 확인.

사전 조건: docker-compose up -d 로 postgres 가 떠 있어야 한다.
기본 pytest 실행에서는 제외됨 (marker: integration). 실행하려면:
    uv run pytest -m integration
"""

from __future__ import annotations

import psycopg
import pytest

from config import DATABASE_URL

pytestmark = pytest.mark.integration


def test_can_connect_to_database():
    with psycopg.connect(DATABASE_URL, connect_timeout=3) as conn, conn.cursor() as cur:
        cur.execute("SELECT 1")
        assert cur.fetchone() == (1,)


def test_vector_extension_is_installed():
    with psycopg.connect(DATABASE_URL, connect_timeout=3) as conn, conn.cursor() as cur:
        cur.execute("SELECT extname FROM pg_extension WHERE extname = 'vector'")
        assert cur.fetchone() == ("vector",)
