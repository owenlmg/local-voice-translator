import asyncio
import time
from pathlib import Path

from .subtitle import parse_srt


class TtsError(RuntimeError):
    pass


def _signed_percent(value: int) -> str:
    return f"+{value}%" if value >= 0 else f"{value}%"


def _signed_hz(value: int) -> str:
    return f"+{value}Hz" if value >= 0 else f"{value}Hz"


async def _synthesize_segment(text: str, voice: str, output_path: Path, rate: int, volume: int, pitch: int) -> None:
    import edge_tts

    communicate = edge_tts.Communicate(
        text,
        voice,
        rate=_signed_percent(rate),
        volume=_signed_percent(volume),
        pitch=_signed_hz(pitch),
    )
    await communicate.save(str(output_path))


def srt_to_voice(
    subtitle_path: Path,
    output_path: Path,
    voice: str,
    engine: str = "auto",
    rate: int = 0,
    volume: int = 0,
    pitch: int = 0,
) -> Path:
    if engine == "local":
        return srt_to_local_voice(subtitle_path, output_path.with_suffix(".wav"), rate=rate)
    if engine == "edge":
        return srt_to_edge_voice(subtitle_path, output_path, voice, rate, volume, pitch)
    try:
        return srt_to_edge_voice(subtitle_path, output_path, voice, rate, volume, pitch)
    except TtsError:
        return srt_to_local_voice(subtitle_path, output_path.with_suffix(".wav"), rate=rate)


def srt_to_edge_voice(
    subtitle_path: Path,
    output_path: Path,
    voice: str,
    rate: int = 0,
    volume: int = 0,
    pitch: int = 0,
) -> Path:
    try:
        from pydub import AudioSegment
    except Exception as exc:
        raise TtsError("pydub is not installed. Install backend requirements first.") from exc

    try:
        import edge_tts  # noqa: F401
    except Exception as exc:
        raise TtsError("edge-tts is not installed. Install backend requirements first.") from exc

    cues = parse_srt(subtitle_path.read_text(encoding="utf-8"))
    segments_dir = output_path.parent / "tts_segments"
    segments_dir.mkdir(parents=True, exist_ok=True)
    combined = AudioSegment.silent(duration=0)

    for cue in cues:
        if cue.start * 1000 > len(combined):
            combined += AudioSegment.silent(duration=int(cue.start * 1000) - len(combined))

        text = cue.text.strip()
        if not text:
            continue

        segment_path = segments_dir / f"{cue.index:05d}.mp3"
        try:
            asyncio.run(_synthesize_segment(text, voice, segment_path, rate, volume, pitch))
            combined += AudioSegment.from_file(segment_path)
        except Exception as exc:
            raise TtsError(f"Edge-TTS failed on cue {cue.index}: {exc}") from exc

        target_end = int(cue.end * 1000)
        if target_end > len(combined):
            combined += AudioSegment.silent(duration=target_end - len(combined))

    combined.export(output_path, format=output_path.suffix.lstrip(".") or "mp3")
    return output_path


def _select_sapi_voice(engine, preferred_language: str = "zh") -> None:
    voices = engine.getProperty("voices")
    preferred = preferred_language.lower()
    for voice in voices:
        haystack = " ".join(str(getattr(voice, field, "")) for field in ("id", "name", "languages")).lower()
        if preferred in haystack or "chinese" in haystack or "huihui" in haystack or "xiaoxiao" in haystack:
            engine.setProperty("voice", voice.id)
            return


def _sapi_segment(text: str, output_path: Path, rate: int) -> None:
    import pyttsx3

    engine = pyttsx3.init()
    _select_sapi_voice(engine)
    base_rate = engine.getProperty("rate") or 180
    engine.setProperty("rate", max(80, int(base_rate + rate * 2)))
    engine.save_to_file(text, str(output_path))
    engine.runAndWait()
    engine.stop()

    for _ in range(50):
        if output_path.exists() and output_path.stat().st_size > 44:
            return
        time.sleep(0.1)
    raise TtsError("Local SAPI TTS did not produce audio.")


def srt_to_local_voice(
    subtitle_path: Path,
    output_path: Path,
    rate: int = 0,
) -> Path:
    try:
        from pydub import AudioSegment
    except Exception as exc:
        raise TtsError("pydub is not installed. Install backend requirements first.") from exc

    cues = parse_srt(subtitle_path.read_text(encoding="utf-8"))
    segments_dir = output_path.parent / "sapi_segments"
    segments_dir.mkdir(parents=True, exist_ok=True)
    combined = AudioSegment.silent(duration=0)

    for cue in cues:
        if cue.start * 1000 > len(combined):
            combined += AudioSegment.silent(duration=int(cue.start * 1000) - len(combined))

        text = cue.text.strip()
        if not text:
            continue

        segment_path = segments_dir / f"{cue.index:05d}.wav"
        _sapi_segment(text, segment_path, rate)
        combined += AudioSegment.from_file(segment_path)

        target_end = int(cue.end * 1000)
        if target_end > len(combined):
            combined += AudioSegment.silent(duration=target_end - len(combined))

    combined.export(output_path, format="wav")
    return output_path
