import json
import shutil
import subprocess
from pathlib import Path

from ..cancel import register_process, unregister_process


class MediaError(RuntimeError):
    pass


def require_ffmpeg() -> None:
    missing = [name for name in ("ffmpeg", "ffprobe") if shutil.which(name) is None]
    if missing:
        raise MediaError(
            "Missing dependency: "
            + ", ".join(missing)
            + ". Install ffmpeg and make sure ffmpeg/ffprobe are available in PATH."
        )


def run_command(args: list[str], job_id: str | None = None) -> subprocess.CompletedProcess[str]:
    require_ffmpeg()
    try:
        process = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding="utf-8")
        if job_id:
            register_process(job_id, process)
        stdout, stderr = process.communicate()
        if job_id:
            unregister_process(job_id, process)
        if process.returncode != 0:
            raise subprocess.CalledProcessError(process.returncode, args, output=stdout, stderr=stderr)
        return subprocess.CompletedProcess(args, process.returncode, stdout, stderr)
    except subprocess.CalledProcessError as exc:
        detail = exc.stderr.strip() or exc.stdout.strip() or str(exc)
        raise MediaError(detail) from exc


def probe_streams(input_path: Path, job_id: str | None = None) -> tuple[bool, bool]:
    result = run_command(
        [
            "ffprobe",
            "-loglevel",
            "error",
            "-show_entries",
            "stream=codec_type",
            "-of",
            "json",
            str(input_path),
        ],
        job_id=job_id,
    )
    data = json.loads(result.stdout or "{}")
    streams = data.get("streams", [])
    has_audio = any(stream.get("codec_type") == "audio" for stream in streams)
    has_video = any(stream.get("codec_type") == "video" for stream in streams)
    return has_audio, has_video


def extract_audio(input_path: Path, output_path: Path, job_id: str | None = None) -> Path:
    run_command(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(input_path),
            "-vn",
            "-acodec",
            "pcm_s16le",
            "-ar",
            "16000",
            "-ac",
            "1",
            str(output_path),
            "-nostdin",
        ],
        job_id=job_id,
    )
    return output_path


def normalize_audio(input_path: Path, output_path: Path, job_id: str | None = None) -> Path:
    run_command(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(input_path),
            "-acodec",
            "pcm_s16le",
            "-ar",
            "16000",
            "-ac",
            "1",
            str(output_path),
            "-nostdin",
        ],
        job_id=job_id,
    )
    return output_path
