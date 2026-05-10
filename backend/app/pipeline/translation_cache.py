import hashlib
import json
from pathlib import Path

from ..config import WORKSPACE_DIR


CACHE_DIR = WORKSPACE_DIR / "translation-cache"


def translation_cache_key(
    source_text: str,
    target_language: str,
    provider: str,
    model: str,
) -> str:
    payload = {
        "source": source_text,
        "target_language": target_language,
        "provider": provider,
        "model": model if provider == "openai" else "",
    }
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def get_cached_translation(key: str) -> str | None:
    path = CACHE_DIR / f"{key}.srt"
    if path.exists():
        return path.read_text(encoding="utf-8")
    return None


def save_cached_translation(key: str, content: str) -> Path:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    path = CACHE_DIR / f"{key}.srt"
    path.write_text(content, encoding="utf-8")
    return path
