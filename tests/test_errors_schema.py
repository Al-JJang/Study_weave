"""NodeError.error_code 가 정의된 ErrorCode Literal 값만 허용하는지 확인."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from schemas.errors import ErrorCode, NodeError


@pytest.mark.parametrize("code", ErrorCode.__args__)
def test_node_error_accepts_defined_error_codes(code):
    error = NodeError(node="parse", error_code=code, message="test")
    assert error.error_code == code


def test_node_error_rejects_unknown_error_code():
    with pytest.raises(ValidationError):
        NodeError(node="parse", error_code="NOT_A_REAL_CODE", message="test")
