from pathlib import Path


class UnsafePathError(ValueError):
    pass


def ensure_within(base_dir: Path, target: Path) -> Path:
    base = base_dir.resolve()
    candidate = target.resolve()
    if not str(candidate).startswith(str(base)):
        raise UnsafePathError(f"Path escapes base directory: {candidate}")
    return candidate


def safe_join(base_dir: Path, relative_path: str) -> Path:
    candidate = base_dir / relative_path
    return ensure_within(base_dir, candidate)
