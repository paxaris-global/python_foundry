import json
from typing import Any


def to_pretty_json(data: Any) -> str:
    return json.dumps(data, indent=2, ensure_ascii=False, sort_keys=True)


def parse_json(text: str) -> dict:
    return json.loads(text)
