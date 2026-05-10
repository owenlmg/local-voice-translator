from pathlib import Path

from .network import normalize_proxy_url


class YoutubeDownloadError(RuntimeError):
    pass


def download_youtube_video(
    url: str,
    output_dir: Path,
    proxy_enabled: bool,
    proxy_url: str,
    ffmpeg_location: str | None = None,
) -> Path:
    try:
        from yt_dlp import YoutubeDL
    except Exception as exc:
        raise YoutubeDownloadError("yt-dlp is not installed. Install backend requirements first.") from exc

    output_dir.mkdir(parents=True, exist_ok=True)
    outtmpl = str(output_dir / "%(title).120B [%(id)s].%(ext)s")
    options = {
        "outtmpl": outtmpl,
        "format": "bv*[ext=mp4]+ba/b[ext=mp4]/b",
        "merge_output_format": "mp4",
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
    }
    if ffmpeg_location:
        options["ffmpeg_location"] = ffmpeg_location
    if proxy_enabled:
        normalized = normalize_proxy_url(proxy_url)
        if normalized:
            options["proxy"] = normalized

    try:
        with YoutubeDL(options) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = Path(ydl.prepare_filename(info))
            if filename.suffix.lower() != ".mp4":
                merged = filename.with_suffix(".mp4")
                if merged.exists():
                    filename = merged
            if not filename.exists():
                candidates = sorted(output_dir.glob("*"), key=lambda path: path.stat().st_mtime, reverse=True)
                media = [path for path in candidates if path.suffix.lower() in {".mp4", ".mkv", ".webm", ".mov", ".m4a", ".mp3"}]
                if media:
                    filename = media[0]
            if not filename.exists():
                raise YoutubeDownloadError("yt-dlp finished but no media file was found.")
            return filename
    except Exception as exc:
        if isinstance(exc, YoutubeDownloadError):
            raise
        raise YoutubeDownloadError(str(exc)) from exc
