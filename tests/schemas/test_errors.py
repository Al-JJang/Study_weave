"""NodeError.error_code 가 정의된 ErrorCode Literal 값만 허용하는지 확인."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from schemas.errors import NodeError


def test_node_error_accepts_defined_error_code():
    error = NodeError(node="parse", error_code="PARSE_FAIL", message="test")
    assert error.error_code == "PARSE_FAIL"


def test_node_error_rejects_unknown_error_code():
    with pytest.raises(ValidationError):
        NodeError(node="parse", error_code="NOT_A_REAL_CODE", message="test")
