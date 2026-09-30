"""업로드·노트 파일을 사용자/날짜 폴더에 안전하게 둔다."""

from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

KST = ZoneInfo("Asia/Seoul")
_UNSAFE = re.compile(r"[^\w.\-가-힣]+", re.UNICODE)


def today_folder() -> str:
    return datetime.now(KST).date().isoformat()


def sanitize_filename(original: str) -> str:
    name = Path(original.replace("\\", "/")).name
    stem = Path(name).stem
    suffix = Path(name).suffix.lower()
    cleaned = _UNSAFE.sub("_", stem)
    cleaned = re.sub(r"_+", "_", cleaned).strip("._")[:80] or "file"
    if suffix and not re.fullmatch(r"\.[a-z0-9]{1,8}", suffix):
        suffix = ""
    return f"{cleaned}{suffix}"


def unique_path(directory: Path, filename: str) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    dest = directory / filename
    if not dest.exists():
        return dest
    stem = Path(filename).stem
    suffix = Path(filename).suffix
    index = 2
    while True:
        candidate = directory / f"{stem}-{index}{suffix}"
        if not candidate.exists():
            return candidate
        index += 1
