import re


def sanitize_text(value: str, max_length: int = 10000) -> str:
    normalized = " ".join(value.split())
    return normalized[:max_length]


def sanitize_feature_list(features: list[str]) -> list[str]:
    cleaned = []
    for feature in features:
        token = re.sub(r"[^a-zA-Z0-9\-_ ]", "", feature).strip().lower()
        if token:
            cleaned.append(token)
    return sorted(set(cleaned))
