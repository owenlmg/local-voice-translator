# Local Voice Pro

[简体中文文档](README.zh-CN.md)

Local Voice Pro is a local web tool for video transcription, subtitle translation, dubbing, and captioned video rendering. It is inspired by the workflow of Voice-Pro, but this project focuses on a smaller, easier-to-run local pipeline built with FastAPI and React.

## What It Does

- Upload local audio or video files.
- Download YouTube videos with `yt-dlp`.
- Extract and normalize audio with FFmpeg.
- Transcribe speech into SRT/VTT/TXT subtitles with Faster-Whisper.
- Translate subtitles with Google Translate or an OpenAI-compatible Chat Completions API.
- Cache translation results to avoid paying twice for the same subtitle translation.
- Generate dubbing audio with Edge-TTS or local Windows SAPI fallback.
- Replace the original video audio track with dubbed audio.
- Burn translated subtitles directly into video frames.
- Stop running jobs from the web UI.
- Continue a job from a later stage, such as download only -> transcribe -> translate -> render.
- Switch the UI between English and Simplified Chinese.

## Use Cases

- Translate a YouTube video into another language.
- Create translated SRT subtitles from local media.
- Render a video with hardcoded translated subtitles.
- Generate a dubbed version of a video for local preview or editing.
- Batch-like iterative workflows where you download first, then decide how far to continue.

## Requirements

- Windows 10/11 is recommended.
- Python 3.10 or newer.
- Node.js 20 or newer.
- FFmpeg and ffprobe.
  - The development copy may include `tools/ffmpeg`, but GitHub releases usually should not include large binaries.
  - If `tools/ffmpeg/bin/ffmpeg.exe` is not present, install FFmpeg globally and add it to PATH.
- Network access for:
  - YouTube downloads.
  - first-time Whisper model downloads.
  - Google Translate, Edge-TTS, or OpenAI-compatible APIs.

## Quick Start

Clone the repository, then run:

```powershell
.\start.bat
```

The script will:

- detect local FFmpeg,
- detect the default proxy at `http://127.0.0.1:7890` if available,
- create or reuse `.venv`,
- install backend dependencies,
- install frontend dependencies,
- start the backend at `http://127.0.0.1:8000`,
- start the frontend at `http://127.0.0.1:5173`,
- open the browser automatically.

Stop services:

```powershell
.\stop.bat
```

## Manual Installation

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r backend\requirements.txt

cd frontend
npm.cmd install
cd ..
```

Start backend:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\start-backend.ps1
```

Start frontend:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\start-frontend.ps1
```

Open:

```text
http://127.0.0.1:5173
```

## Proxy

The UI has a proxy setting, defaulting to:

```text
http://127.0.0.1:7890
```

The proxy is used for YouTube downloads, Google Translate, Edge-TTS, and OpenAI-compatible API calls when enabled.

## OpenAI-Compatible Translation

In the UI, expand settings and choose:

```text
ChatGPT / OpenAI-compatible API
```

Then fill in:

- API Key
- Base URL, for example `https://api.openai.com/v1`
- Model, for example `gpt-4o-mini`

The key is saved only in browser localStorage on your machine.

## Generated Files

Each job writes to:

```text
workspace/jobs/{job_id}/
```

Common outputs:

- `source.wav`
- `original.srt`
- `original.vtt`
- `original.txt`
- `translated.srt`
- `dubbed.mp3`
- `dubbed.wav`
- `dubbed_video.mp4`
- `translated_subtitles_video.mp4`
- `manifest.json`

Translation cache is stored in:

```text
workspace/translation-cache/
```

## Notes

- Hardcoded subtitles require re-encoding video. Use CRF and preset settings to balance file size, speed, and quality.
- Local Windows SAPI voices depend on voices installed on the system.
- Edge-TTS can be unstable for some voices or networks; use local TTS fallback when needed.
- Faster-Whisper downloads models on first use.
