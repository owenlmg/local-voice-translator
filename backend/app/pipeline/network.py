import os


def normalize_proxy_url(proxy_url: str) -> str:
    value = proxy_url.strip()
    if not value:
        return ""
    if "://" not in value:
        value = f"http://{value}"
    return value


def proxy_dict(proxy_enabled: bool, proxy_url: str) -> dict[str, str] | None:
    if not proxy_enabled:
        return None
    normalized = normalize_proxy_url(proxy_url)
    if not normalized:
        return None
    return {"http": normalized, "https": normalized}


def apply_proxy(proxy_enabled: bool, proxy_url: str) -> str:
    normalized = normalize_proxy_url(proxy_url) if proxy_enabled else ""
    keys = ("HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY", "http_proxy", "https_proxy", "all_proxy")
    if normalized:
        for key in keys:
            os.environ[key] = normalized
        return normalized

    for key in keys:
        os.environ.pop(key, None)
    return ""

