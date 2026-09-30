"""팀원 전용 사용자. 인증 없이 사이드바에서 고른다."""

from __future__ import annotations

from fastapi import HTTPException

TEAM_USERS: tuple[tuple[str, str], ...] = (
    ("seoyoung", "서영"),
    ("songju", "송주"),
    ("saegyeol", "새결"),
    ("donggyu", "동규"),
)
USER_IDS = {user_id for user_id, _ in TEAM_USERS}
USER_NAMES = dict(TEAM_USERS)

MISSING_USER_DETAIL = "user_id가 필요합니다. 서영, 송주, 새결, 동규 중 하나를 선택하세요."
UNKNOWN_USER_DETAIL = "알 수 없는 사용자입니다. 서영, 송주, 새결, 동규 중 하나를 선택하세요."


def require_user_id(user_id: str | None) -> str:
    if user_id is None or not str(user_id).strip():
        raise HTTPException(status_code=400, detail=MISSING_USER_DETAIL)
    uid = str(user_id).strip()
    if uid not in USER_IDS:
        raise HTTPException(status_code=400, detail=UNKNOWN_USER_DETAIL)
    return uid


def list_team_users() -> list[dict[str, str]]:
    return [{"id": user_id, "name": name} for user_id, name in TEAM_USERS]
