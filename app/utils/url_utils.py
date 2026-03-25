from urllib.parse import urlparse


TRUSTED_SCHEMES = {"http", "https"}


def normalize_url(url: str) -> str:
    value = url.strip()
    if value.endswith("/"):
        value = value[:-1]
    return value


def domain_of(url: str) -> str:
    parsed = urlparse(url)
    return parsed.netloc.lower().replace("www.", "")


def is_safe_url(url: str) -> bool:
    parsed = urlparse(url)
    return parsed.scheme in TRUSTED_SCHEMES and bool(parsed.netloc)
