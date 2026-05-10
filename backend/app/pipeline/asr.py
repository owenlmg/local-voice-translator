from pathlib import Path

from .subtitle import cues_from_segments, cues_to_srt, cues_to_txt, cues_to_vtt


class AsrError(RuntimeError):
    pass


def transcribe_audio(
    audio_path: Path,
    output_dir: Path,
    model_name: str,
    source_language: str,
) -> dict[str, Path]:
    try:
        from faster_whisper import WhisperModel
    except Exception as exc:
        raise AsrError("faster-whisper is not installed. Install backend requirements first.") from exc

    language = None if source_language.lower() in {"auto", "automatic", ""} else source_language

    try:
        model = WhisperModel(model_name, device="auto", compute_type="default")
        segments, _info = model.transcribe(str(audio_path), language=language, vad_filter=True)
        segment_dicts = [
            {"start": segment.start, "end": segment.end, "text": segment.text}
            for segment in segments
        ]
    except Exception as exc:
        raise AsrError(str(exc)) from exc

    cues = cues_from_segments(segment_dicts)
    srt_path = output_dir / "original.srt"
    vtt_path = output_dir / "original.vtt"
    txt_path = output_dir / "original.txt"
    srt_path.write_text(cues_to_srt(cues), encoding="utf-8")
    vtt_path.write_text(cues_to_vtt(cues), encoding="utf-8")
    txt_path.write_text(cues_to_txt(cues), encoding="utf-8")
    return {"srt": srt_path, "vtt": vtt_path, "txt": txt_path}

