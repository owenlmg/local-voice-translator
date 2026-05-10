from pathlib import Path

from ..cancel import JobCancelled, check_cancelled
from ..config import ROOT_DIR
from ..models import JobManifest, JobStatus
from ..store import job_dir, save_manifest
from .asr import transcribe_audio
from .media import extract_audio, normalize_audio, probe_streams
from .mux import add_subtitle_track, replace_audio
from .network import apply_proxy
from .translate import translate_srt
from .translation_cache import get_cached_translation, save_cached_translation, translation_cache_key
from .tts import srt_to_voice
from .youtube import download_youtube_video


def _checkpoint(manifest: JobManifest, stage: str, progress: int, log: str | None = None) -> None:
    check_cancelled(manifest)
    manifest.status = JobStatus.running
    manifest.set_stage(stage, progress)
    if log:
        manifest.add_log(log)
    save_manifest(manifest)
    check_cancelled(manifest)


def _existing(path: Path) -> Path | None:
    return path if path.exists() and path.stat().st_size > 0 else None


def _detect_video_state(manifest: JobManifest, input_path: Path) -> tuple[bool, bool]:
    check_cancelled(manifest)
    has_audio, has_video = probe_streams(input_path, manifest.id)
    manifest.has_audio = has_audio
    manifest.has_video = has_video
    return has_audio, has_video


def run_full_pipeline(manifest: JobManifest) -> None:
    output_dir = job_dir(manifest.id)
    try:
        proxy = apply_proxy(manifest.options.proxy_enabled, manifest.options.proxy_url)
        manifest.add_log(f"Proxy {'enabled: ' + proxy if proxy else 'disabled'}.")
        save_manifest(manifest)
        check_cancelled(manifest)

        input_path = Path(manifest.input_path) if manifest.input_path else None
        if manifest.source_type == "youtube" and (input_path is None or not input_path.exists()):
            _checkpoint(manifest, "Downloading YouTube video", 5, "Downloading media with yt-dlp.")
            ffmpeg_location = ROOT_DIR / "tools" / "ffmpeg" / "bin"
            downloaded = download_youtube_video(
                manifest.source_url or "",
                output_dir,
                manifest.options.proxy_enabled,
                manifest.options.proxy_url,
                str(ffmpeg_location) if ffmpeg_location.exists() else None,
            )
            manifest.input_path = str(downloaded)
            manifest.input_name = downloaded.name
            manifest.upsert_artifact("source_media", "Downloaded video", "media", downloaded)
            save_manifest(manifest)
            check_cancelled(manifest)

        input_path = Path(manifest.input_path)
        if not input_path.exists():
            raise RuntimeError("Input media file does not exist.")

        if manifest.options.pipeline_step == "download":
            manifest.status = JobStatus.completed
            manifest.set_stage("Downloaded", 100)
            manifest.add_log("Stopped after media download.")
            return

        _checkpoint(manifest, "Inspecting media", 5, "Checking streams with ffprobe.")
        has_audio, has_video = _detect_video_state(manifest, input_path)
        if not has_audio:
            raise RuntimeError("Uploaded media has no audio stream.")

        source_audio = output_dir / "source.wav"
        if _existing(source_audio):
            _checkpoint(manifest, "Audio ready", 15, "Using existing extracted audio.")
        else:
            _checkpoint(manifest, "Extracting audio", 15, "Extracting normalized 16 kHz mono audio.")
            if has_video:
                extract_audio(input_path, source_audio, manifest.id)
            else:
                normalize_audio(input_path, source_audio, manifest.id)
        manifest.upsert_artifact("source_audio", "Source audio", "audio", source_audio)
        save_manifest(manifest)
        check_cancelled(manifest)

        original_srt = output_dir / "original.srt"
        original_vtt = output_dir / "original.vtt"
        original_txt = output_dir / "original.txt"
        if _existing(original_srt) and _existing(original_vtt) and _existing(original_txt):
            _checkpoint(manifest, "Subtitles ready", 35, "Using existing recognized subtitles.")
            subtitle_paths = {"srt": original_srt, "vtt": original_vtt, "txt": original_txt}
        else:
            _checkpoint(manifest, "Recognizing subtitles", 35, f"Running faster-whisper model {manifest.options.whisper_model}.")
            subtitle_paths = transcribe_audio(
                source_audio,
                output_dir,
                manifest.options.whisper_model,
                manifest.options.source_language,
            )
            check_cancelled(manifest)
        manifest.upsert_artifact("original_srt", "Original SRT", "subtitle", subtitle_paths["srt"])
        manifest.upsert_artifact("original_vtt", "Original VTT", "subtitle", subtitle_paths["vtt"])
        manifest.upsert_artifact("original_txt", "Original TXT", "text", subtitle_paths["txt"])
        save_manifest(manifest)

        if manifest.options.pipeline_step == "subtitle":
            manifest.status = JobStatus.completed
            manifest.set_stage("Subtitles ready", 100)
            manifest.add_log("Stopped after subtitle recognition.")
            return

        translated_srt = output_dir / "translated.srt"
        if _existing(translated_srt) and not manifest.options.force_retranslate:
            _checkpoint(manifest, "Translation ready", 58, "Using existing translated subtitles.")
        else:
            source_content = subtitle_paths["srt"].read_text(encoding="utf-8")
            cache_key = translation_cache_key(
                source_content,
                manifest.options.target_language,
                manifest.options.translation_provider,
                manifest.options.openai_model,
            )
            cached = get_cached_translation(cache_key) if not manifest.options.force_retranslate else None
            if cached:
                translated_srt.write_text(cached, encoding="utf-8")
                manifest.add_log("Using cached translation result.")
            else:
                _checkpoint(
                    manifest,
                    "Translating subtitles",
                    58,
                    f"Translating to {manifest.options.target_language} with {manifest.options.translation_provider}.",
                )
                _, warnings = translate_srt(
                    subtitle_paths["srt"],
                    translated_srt,
                    manifest.options.source_language,
                    manifest.options.target_language,
                    manifest.options.proxy_enabled,
                    manifest.options.proxy_url,
                    manifest.options.translation_provider,
                    manifest.options.openai_api_key,
                    manifest.options.openai_base_url,
                    manifest.options.openai_model,
                )
                for warning in warnings:
                    manifest.add_log(warning)
                save_cached_translation(cache_key, translated_srt.read_text(encoding="utf-8"))
                manifest.add_log("Saved translation result to cache.")
                check_cancelled(manifest)
            manifest.options.force_retranslate = False
        manifest.upsert_artifact("translated_srt", "Translated SRT", "subtitle", translated_srt)
        save_manifest(manifest)

        if manifest.options.pipeline_step == "translate":
            manifest.status = JobStatus.completed
            manifest.set_stage("Translation ready", 100)
            manifest.add_log("Stopped after subtitle translation.")
            return

        if manifest.options.pipeline_step == "caption":
            if not has_video:
                has_audio, has_video = _detect_video_state(manifest, input_path)
            if not has_video:
                raise RuntimeError("Subtitle video output requires a video input.")
            _checkpoint(
                manifest,
                "Burning subtitles into video",
                82,
                f"Hardcoding translated subtitles into the video frames. preset={manifest.options.caption_preset}, crf={manifest.options.caption_crf}.",
            )
            subtitled_video = output_dir / "translated_subtitles_video.mp4"
            add_subtitle_track(
                input_path,
                translated_srt,
                subtitled_video,
                manifest.id,
                manifest.options.caption_preset,
                manifest.options.caption_crf,
            )
            manifest.upsert_artifact("subtitled_video", "Video with translated subtitles", "video", subtitled_video)
            manifest.status = JobStatus.completed
            manifest.set_stage("Subtitled video ready", 100)
            manifest.add_log("Stopped after adding translated subtitles to video.")
            return

        _checkpoint(manifest, "Generating dubbing", 78, f"Generating Edge-TTS voice {manifest.options.tts_voice}.")
        use_local = manifest.options.tts_engine == "local"
        dubbed_audio = output_dir / ("dubbed.wav" if use_local else "dubbed.mp3")
        dubbed_audio = srt_to_voice(
            translated_srt,
            dubbed_audio,
            manifest.options.tts_voice,
            manifest.options.tts_engine,
            manifest.options.tts_rate,
            manifest.options.tts_volume,
            manifest.options.tts_pitch,
        )
        check_cancelled(manifest)
        manifest.upsert_artifact("dubbed_audio", "Dubbed audio", "audio", dubbed_audio)
        save_manifest(manifest)

        if has_video:
            _checkpoint(manifest, "Muxing video", 92, "Replacing the original video audio track.")
            output_video = output_dir / "dubbed_video.mp4"
            replace_audio(input_path, dubbed_audio, output_video, manifest.id)
            manifest.upsert_artifact("dubbed_video", "Dubbed video", "video", output_video)

        manifest.status = JobStatus.completed
        manifest.set_stage("Completed", 100)
        manifest.add_log("Job completed.")
    except JobCancelled:
        pass
    except Exception as exc:
        manifest.status = JobStatus.failed
        manifest.error = str(exc)
        manifest.add_log(f"Failed: {exc}")
    finally:
        save_manifest(manifest)


def rerun_dubbing(manifest: JobManifest) -> None:
    output_dir = job_dir(manifest.id)
    input_path = Path(manifest.input_path)
    translated_srt = output_dir / "translated.srt"
    try:
        proxy = apply_proxy(manifest.options.proxy_enabled, manifest.options.proxy_url)
        manifest.add_log(f"Proxy {'enabled: ' + proxy if proxy else 'disabled'}.")
        save_manifest(manifest)
        check_cancelled(manifest)

        if not translated_srt.exists():
            raise RuntimeError("Translated subtitle file does not exist.")
        _checkpoint(manifest, "Regenerating dubbing", 70, "Using edited translated subtitles.")
        use_local = manifest.options.tts_engine == "local"
        dubbed_audio = output_dir / ("dubbed.wav" if use_local else "dubbed.mp3")
        dubbed_audio = srt_to_voice(
            translated_srt,
            dubbed_audio,
            manifest.options.tts_voice,
            manifest.options.tts_engine,
            manifest.options.tts_rate,
            manifest.options.tts_volume,
            manifest.options.tts_pitch,
        )
        check_cancelled(manifest)
        manifest.upsert_artifact("dubbed_audio", "Dubbed audio", "audio", dubbed_audio)
        if manifest.has_video:
            output_video = output_dir / "dubbed_video.mp4"
            replace_audio(input_path, dubbed_audio, output_video, manifest.id)
            manifest.upsert_artifact("dubbed_video", "Dubbed video", "video", output_video)
        manifest.status = JobStatus.completed
        manifest.set_stage("Completed", 100)
        manifest.add_log("Dubbing regenerated from edited subtitles.")
    except JobCancelled:
        pass
    except Exception as exc:
        manifest.status = JobStatus.failed
        manifest.error = str(exc)
        manifest.add_log(f"Failed: {exc}")
    finally:
        save_manifest(manifest)


def continue_pipeline(manifest: JobManifest) -> None:
    run_full_pipeline(manifest)


def render_caption_only(manifest: JobManifest) -> None:
    output_dir = job_dir(manifest.id)
    input_path = Path(manifest.input_path)
    translated_srt = output_dir / "translated.srt"
    try:
        if not input_path.exists():
            raise RuntimeError("Input media file does not exist.")
        if not translated_srt.exists():
            raise RuntimeError("Translated subtitle file does not exist.")
        _checkpoint(manifest, "Inspecting media", 10, "Checking streams with ffprobe.")
        _has_audio, has_video = _detect_video_state(manifest, input_path)
        if not has_video:
            raise RuntimeError("Subtitle video output requires a video input.")
        _checkpoint(
            manifest,
            "Burning subtitles into video",
            60,
            f"Hardcoding translated subtitles into the video frames. preset={manifest.options.caption_preset}, crf={manifest.options.caption_crf}.",
        )
        subtitled_video = output_dir / "translated_subtitles_video.mp4"
        add_subtitle_track(
            input_path,
            translated_srt,
            subtitled_video,
            manifest.id,
            manifest.options.caption_preset,
            manifest.options.caption_crf,
        )
        manifest.upsert_artifact("subtitled_video", "Video with translated subtitles", "video", subtitled_video)
        manifest.status = JobStatus.completed
        manifest.set_stage("Subtitled video ready", 100)
        manifest.add_log("Subtitled video generated from edited subtitles.")
    except JobCancelled:
        pass
    except Exception as exc:
        manifest.status = JobStatus.failed
        manifest.error = str(exc)
        manifest.add_log(f"Failed: {exc}")
    finally:
        save_manifest(manifest)
