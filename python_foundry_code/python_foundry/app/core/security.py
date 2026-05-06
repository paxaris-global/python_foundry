import hashlib
import re
from typing import Iterable


def sanitize_project_name(name: str) -> str:
    safe = re.sub(r"[^a-zA-Z0-9\-_]", "-", name).strip("-")
    return safe.lower() or "generated-app"


def stable_hash(parts: Iterable[str]) -> str:
    joined = "::".join(parts)
    return hashlib.sha256(joined.encode("utf-8")).hexdigest()
