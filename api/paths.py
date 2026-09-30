"""업로드·노트 파일을 사용자/날짜 폴더에 안전하게 둔다."""

from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path
from typing import Literal
from zoneinfo import ZoneInfo

KST = ZoneInfo("Asia/Seoul")
_UNSAFE = re.compile(r"[^\w.\-가-힣]+", re.UNICODE)

MaterialKind = Literal["lecture", "code"]
CODE_SUFFIXES = {".py", ".js", ".ts", ".tsx", ".jsx", ".java", ".go", ".rs", ".c", ".cpp"}
FOLDER_TEXT_SUFFIXES = CODE_SUFFIXES | {
    ".md",
    ".txt",
    ".json",
    ".toml",
    ".yml",
    ".yaml",
    ".ipynb",
    ".sql",
    ".sh",
    ".html",
    ".css",
}
SKIP_DIR_NAMES = frozenset(
    {
        ".git",
        ".hg",
        ".svn",
        ".venv",
        "venv",
        "node_modules",
        "__pycache__",
        ".idea",
        ".vscode",
        ".next",
        "dist",
        "build",
        "coverage",
        ".pytest_cache",
        ".mypy_cache",
        ".ruff_cache",
    }
)
SKIP_FILE_NAMES = frozenset({".ds_store", "thumbs.db", ".gitignore", ".env"})
SKIP_SUFFIXES = {
    ".pyc",
    ".pyo",
    ".so",
    ".dylib",
    ".dll",
    ".exe",
    ".zip",
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".webp",
    ".pdf",
}
SPECIAL_CODE_NAMES = frozenset({"makefile", "dockerfile", "procfile"})
MAX_REL_DEPTH = 8


def parse_material_kind(raw: str | None, *, filename: str) -> MaterialKind:
    text = (raw or "").strip().lower()
    if text == "code":
        return "code"
    if text == "lecture":
        return "lecture"
    suffix = Path(filename).suffix.lower()
    if suffix in CODE_SUFFIXES:
        return "code"
    return "lecture"


def today_folder() -> str:
    return datetime.now(KST).date().isoformat()


def parse_study_date(raw: str | None) -> str:
    text = (raw or "").strip()
    if not text:
        return today_folder()
    try:
        if re.fullmatch(r"\d{4}-\d{2}-\d{2}", text):
            datetime.strptime(text, "%Y-%m-%d")
            return text
        match = re.fullmatch(r"(\d{1,2})[./-](\d{1,2})", text)
        if match:
            month = int(match.group(1))
            day = int(match.group(2))
            return datetime(2026, month, day, tzinfo=KST).date().isoformat()
    except ValueError as exc:
        raise ValueError("날짜는 YYYY-MM-DD 또는 7/21 형식으로 넣어 주세요.") from exc
    raise ValueError("날짜는 YYYY-MM-DD 또는 7/21 형식으로 넣어 주세요.")


def normalize_topic(raw: str | None) -> str:
    text = (raw or "").strip()
    if not text:
        return "미분류"
    cleaned = _UNSAFE.sub(" ", text)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()[:40]
    return cleaned or "미분류"


def topic_slug(topic: str) -> str:
    cleaned = _UNSAFE.sub("_", topic.strip())
    cleaned = re.sub(r"_+", "_", cleaned).strip("._")[:40]
    return cleaned or "unfiled"


def sanitize_filename(original: str) -> str:
    name = Path(original.replace("\\", "/")).name
    stem = Path(name).stem
    suffix = Path(name).suffix.lower()
    cleaned = _UNSAFE.sub("_", stem)
    cleaned = re.sub(r"_+", "_", cleaned).strip("._")[:80] or "file"
    if suffix and not re.fullmatch(r"\.[a-z0-9]{1,8}", suffix):
        suffix = ""
    return f"{cleaned}{suffix}"


def normalize_relpath(raw: str | None) -> str:
    text = (raw or "").replace("\\", "/").strip().lstrip("/")
    parts: list[str] = []
    for part in text.split("/"):
        if not part or part == ".":
            continue
        if part == "..":
            raise ValueError("상대 경로에 .. 를 넣을 수 없습니다.")
        parts.append(part)
    if not parts:
        raise ValueError("파일 경로가 필요합니다.")
    if len(parts) > MAX_REL_DEPTH:
        raise ValueError("폴더 깊이가 너무 깊습니다.")
    return "/".join(parts)


def strip_root_segment(relpath: str) -> str:
    parts = relpath.split("/")
    if len(parts) <= 1:
        return relpath
    return "/".join(parts[1:])


def should_skip_relpath(relpath: str) -> bool:
    parts = [part.lower() for part in relpath.split("/") if part]
    if any(part in SKIP_DIR_NAMES or part.startswith(".") for part in parts[:-1]):
        return True
    name = parts[-1] if parts else ""
    suffix = Path(name).suffix.lower()
    if name in SKIP_FILE_NAMES or suffix in SKIP_SUFFIXES:
        return True
    return name.startswith(".") and name not in SPECIAL_CODE_NAMES


def is_code_folder_file(relpath: str) -> bool:
    name = Path(relpath).name.lower()
    if name in SPECIAL_CODE_NAMES or name in {"requirements.txt", "pyproject.toml", "package.json"}:
        return True
    return Path(name).suffix.lower() in FOLDER_TEXT_SUFFIXES


def sanitize_relpath(raw: str | None) -> str:
    rel = normalize_relpath(raw)
    if should_skip_relpath(rel):
        raise ValueError("이 경로는 건너뜁니다.")
    parts = rel.split("/")
    cleaned = [
        sanitize_filename(part) if index == len(parts) - 1 else topic_slug(part) or "folder"
        for index, part in enumerate(parts)
    ]
    return "/".join(cleaned)


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
