from pathlib import Path
import json
import re
import time

from .network import normalize_proxy_url, proxy_dict
from .subtitle import Cue, cues_to_srt, parse_srt


class TranslateError(RuntimeError):
    pass


ERROR_TEXT_RE = re.compile(r"Error\s+\d+|Server Error|That.s an error", re.IGNORECASE)


def _converter(target_language: str):
    if target_language != "zh-CN":
        return None, []
    try:
        from opencc import OpenCC

        return OpenCC("t2s"), []
    except Exception as exc:
        return None, [f"OpenCC is unavailable; Chinese simplification skipped. {exc}"]


def _finalize_text(text: str, converter) -> str:
    value = text.strip()
    return converter.convert(value) if converter else value


def _looks_like_failed_translation(text: str) -> bool:
    return bool(ERROR_TEXT_RE.search(text))


def translate_srt(
    input_srt: Path,
    output_srt: Path,
    source_language: str,
    target_language: str,
    proxy_enabled: bool = True,
    proxy_url: str = "http://127.0.0.1:7890",
    provider: str = "google",
    openai_api_key: str = "",
    openai_base_url: str = "https://api.openai.com/v1",
    openai_model: str = "gpt-4o-mini",
) -> tuple[Path, list[str]]:
    cues = parse_srt(input_srt.read_text(encoding="utf-8"))
    converter, warnings = _converter(target_language)

    if provider == "openai":
        translated, llm_warnings = translate_cues_openai(
            cues,
            target_language,
            openai_api_key,
            openai_base_url,
            openai_model,
            proxy_enabled,
            proxy_url,
        )
        warnings.extend(llm_warnings)
        for cue in cues:
            if cue.index in translated:
                cue.text = _finalize_text(translated[cue.index], converter)
        output_srt.write_text(cues_to_srt(cues), encoding="utf-8")
        return output_srt, warnings

    google_warnings = translate_cues_google(cues, source_language, target_language, proxy_enabled, proxy_url, converter)
    warnings.extend(google_warnings)
    output_srt.write_text(cues_to_srt(cues), encoding="utf-8")
    return output_srt, warnings


def translate_cues_google(
    cues: list[Cue],
    source_language: str,
    target_language: str,
    proxy_enabled: bool,
    proxy_url: str,
    converter,
) -> list[str]:
    try:
        from deep_translator import GoogleTranslator
    except Exception as exc:
        raise TranslateError("deep-translator is not installed. Install backend requirements first.") from exc

    source = "auto" if source_language.lower() in {"auto", "automatic", ""} else source_language
    translator = GoogleTranslator(
        source=source,
        target=target_language,
        proxies=proxy_dict(proxy_enabled, proxy_url),
    )
    warnings: list[str] = []

    for cue in cues:
        text = cue.text.strip()
        if not text:
            continue
        last_error: Exception | None = None
        for attempt in range(3):
            try:
                translated = translator.translate(text)
                if translated and not _looks_like_failed_translation(translated):
                    cue.text = _finalize_text(translated, converter)
                    last_error = None
                    break
                last_error = TranslateError(translated or "Empty translation")
            except Exception as exc:
                last_error = exc
            time.sleep(0.8 * (attempt + 1))
        if last_error:
            cue.text = _finalize_text(text, converter)
            warnings.append(f"Translation failed for cue {cue.index}; kept original text. {last_error}")
    return warnings


def _chunks(items: list[Cue], size: int) -> list[list[Cue]]:
    return [items[index : index + size] for index in range(0, len(items), size)]


def _extract_json_array(content: str) -> list[dict]:
    text = content.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?", "", text).strip()
        text = re.sub(r"```$", "", text).strip()
    match = re.search(r"\[[\s\S]*\]", text)
    if match:
        text = match.group(0)
    data = json.loads(text)
    if not isinstance(data, list):
        raise TranslateError("Model response is not a JSON array.")
    return data


def translate_cues_openai(
    cues: list[Cue],
    target_language: str,
    api_key: str,
    base_url: str,
    model: str,
    proxy_enabled: bool,
    proxy_url: str,
) -> tuple[dict[int, str], list[str]]:
    if not api_key:
        raise TranslateError("OpenAI API key is required for ChatGPT translation.")
    try:
        import httpx
    except Exception as exc:
        raise TranslateError("httpx is not installed. Install backend requirements first.") from exc

    endpoint = normalize_proxy_url(base_url).rstrip("/") + "/chat/completions"
    proxies = proxy_dict(proxy_enabled, proxy_url)
    client_kwargs = {"timeout": 180.0}
    if proxies:
        client_kwargs["proxy"] = proxies["https"]

    translated: dict[int, str] = {}
    warnings: list[str] = []
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

    system_prompt = (
        "You are a professional subtitle translator. Translate subtitles accurately and naturally. "
        "Preserve meaning, tone, names, numbers, and timing context. "
        "Return only a JSON array. Each item must be {\"index\": number, \"text\": string}. "
        "Do not include markdown or explanations."
    )

    with httpx.Client(**client_kwargs) as client:
        for chunk in _chunks([cue for cue in cues if cue.text.strip()], 30):
            payload_items = [{"index": cue.index, "text": cue.text.strip()} for cue in chunk]
            user_prompt = (
                f"Translate these subtitle lines to {target_language}. "
                "Keep each line concise for subtitles. Return all indexes exactly once.\n"
                + json.dumps(payload_items, ensure_ascii=False)
            )
            body = {
                "model": model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                "temperature": 0.2,
            }

            last_error: Exception | None = None
            for attempt in range(3):
                try:
                    response = client.post(endpoint, headers=headers, json=body)
                    response.raise_for_status()
                    content = response.json()["choices"][0]["message"]["content"]
                    for item in _extract_json_array(content):
                        index = int(item["index"])
                        text = str(item["text"]).strip()
                        if text:
                            translated[index] = text
                    last_error = None
                    break
                except Exception as exc:
                    last_error = exc
                    time.sleep(1.2 * (attempt + 1))
            if last_error:
                indexes = ", ".join(str(cue.index) for cue in chunk)
                warnings.append(f"OpenAI translation failed for cues {indexes}; kept original text. {last_error}")

    return translated, warnings
