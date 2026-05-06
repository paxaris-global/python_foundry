import os
from pathlib import Path


def ensure_directory(path: str | Path) -> Path:
    target = Path(path)
    target.mkdir(parents=True, exist_ok=True)
    return target


def write_text_file(path: str | Path, content: str) -> None:
    target = Path(path)
    ensure_directory(target.parent)
    target.write_text(content, encoding="utf-8")


def list_files_recursive(root: str | Path) -> list[Path]:
    root_path = Path(root)
    if not root_path.exists():
        return []
    return [p for p in root_path.rglob("*") if p.is_file()]


def is_text_file(path: Path) -> bool:
    try:
        with open(path, "r", encoding="utf-8"):
            return True
    except (UnicodeDecodeError, OSError):
        return False


def safe_relative_path(base: str | Path, child: str | Path) -> str:
    return os.path.relpath(str(child), str(base)).replace("\\", "/")
