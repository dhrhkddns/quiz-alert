"""실행 파일/소스 모두에서 questions.json 위치를 찾는다."""

from __future__ import annotations

import sys
from pathlib import Path


def is_frozen() -> bool:
    return bool(getattr(sys, "frozen", False))


def app_dir() -> Path:
    """실행 파일이 있는 폴더. exe 옆의 questions.json 을 우선 읽는다."""
    if is_frozen():
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


def bundled_dir() -> Path:
    """PyInstaller 로 묶인 리소스 폴더."""
    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:
        return Path(meipass)
    return app_dir()


def resolve_questions_path() -> Path:
    external = app_dir() / "questions.json"
    if external.is_file():
        return external
    return bundled_dir() / "questions.json"


def progress_path() -> Path:
    return app_dir() / ".quiz_progress.json"
