from pathlib import Path

from .media import run_command


def replace_audio(video_path: Path, audio_path: Path, output_path: Path, job_id: str | None = None) -> Path:
    run_command(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(video_path),
            "-i",
            str(audio_path),
            "-c:v",
            "copy",
            "-map",
            "0:v:0",
            "-map",
            "1:a:0",
            "-c:a",
            "aac",
            "-shortest",
            str(output_path),
            "-nostdin",
        ],
        job_id=job_id,
    )
    return output_path


def add_subtitle_track(
    video_path: Path,
    subtitle_path: Path,
    output_path: Path,
    job_id: str | None = None,
    preset: str = "medium",
    crf: int = 28,
) -> Path:
    allowed_presets = {"ultrafast", "superfast", "veryfast", "faster", "fast", "medium", "slow"}
    preset = preset if preset in allowed_presets else "medium"
    crf = max(18, min(35, int(crf)))
    subtitle_filter_path = _escape_subtitles_filter_path(subtitle_path)
    force_style = (
        "FontName=Microsoft YaHei,"
        "FontSize=20,"
        "PrimaryColour=&H00FFFFFF,"
        "OutlineColour=&H00000000,"
        "BorderStyle=1,"
        "Outline=2,"
        "Shadow=0,"
        "MarginV=36"
    )
    run_command(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(video_path),
            "-vf",
            f"subtitles='{subtitle_filter_path}':force_style='{force_style}'",
            "-c:v",
            "libx264",
            "-crf",
            str(crf),
            "-preset",
            preset,
            "-c:a",
            "copy",
            "-movflags",
            "+faststart",
            str(output_path),
            "-nostdin",
        ],
        job_id=job_id,
    )
    return output_path


def _escape_subtitles_filter_path(path: Path) -> str:
    value = path.resolve().as_posix()
    value = value.replace(":", r"\:")
    value = value.replace("'", r"\'")
    return value
