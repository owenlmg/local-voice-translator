# Local Voice Pro

[English README](README.md)

Local Voice Pro 是一个本地 Web 工具，用于视频转写、字幕翻译、配音和字幕视频生成。它参考了 Voice-Pro 的工作流，但目标是提供一个更轻量、容易在本机运行的 FastAPI + React 版本。

## 功能简介

- 上传本地音频或视频。
- 使用 `yt-dlp` 下载 YouTube 视频。
- 使用 FFmpeg 提取和规范化音频。
- 使用 Faster-Whisper 识别语音并生成 SRT/VTT/TXT 字幕。
- 使用 Google 翻译或 OpenAI 兼容的 Chat Completions API 翻译字幕。
- 自动缓存翻译结果，避免同一份字幕重复调用付费 API。
- 使用 Edge-TTS 生成配音，并在可用时支持本地系统 TTS 兜底。
- 将配音音轨合成回视频。
- 将翻译字幕硬字幕烧录到视频画面。
- 可在网页中停止正在运行的任务。
- 可从中间阶段继续任务，例如只下载视频后继续识别、翻译、生成字幕视频或完整配音。
- 支持英文和简体中文界面切换。

## 适用场景

- 将 YouTube 视频翻译成另一种语言。
- 从本地视频或音频生成翻译字幕。
- 生成带硬字幕的视频。
- 生成配音版视频，便于本地预览或后续剪辑。
- 分阶段处理：先下载，再决定是否继续识别、翻译、配音或烧录字幕。

## 环境要求

- 支持 Windows 10/11、macOS 和 Linux。
- Python 3.10 或更高版本。
- Node.js 20 或更高版本。
- FFmpeg 和 ffprobe。
  - Windows：全局安装 FFmpeg，或放到 `tools/ffmpeg/bin`。
  - macOS：`brew install ffmpeg`
  - Ubuntu/Debian：`sudo apt update && sudo apt install -y ffmpeg`
- 可选本地 TTS 依赖：
  - Linux：如果要使用本地系统 TTS，可安装 `espeak-ng`，例如 `sudo apt install -y espeak-ng`。
  - macOS/Windows：本地音色来自操作系统已安装语音。
- 以下功能需要联网：
  - YouTube 下载。
  - 首次下载 Whisper 模型。
  - Google 翻译、Edge-TTS 或 OpenAI 兼容 API。

## 一键启动

克隆项目后，根据系统运行对应启动脚本。

Windows：

```powershell
.\start.bat
```

macOS/Linux：

```bash
chmod +x start.sh stop.sh scripts/*.sh
./start.sh
```

脚本会自动：

- 检查本地 FFmpeg，
- 检测默认代理 `http://127.0.0.1:7890`，
- 创建或复用 `.venv`，
- 安装后端依赖，
- 安装前端依赖，
- 启动后端 `http://127.0.0.1:8000`，
- 启动前端 `http://127.0.0.1:5173`，
- 自动打开浏览器。

停止服务：

Windows：

```powershell
.\stop.bat
```

macOS/Linux：

```bash
./stop.sh
```

## 手动安装

Windows PowerShell：

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r backend\requirements.txt

cd frontend
npm.cmd install
cd ..
```

macOS/Linux：

```bash
python3 -m venv .venv
./.venv/bin/python -m pip install --upgrade pip
./.venv/bin/python -m pip install -r backend/requirements.txt

cd frontend
npm install
cd ..
```

Windows 启动后端：

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\start-backend.ps1
```

Windows 启动前端：

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\start-frontend.ps1
```

macOS/Linux 启动后端：

```bash
./scripts/start-backend.sh
```

macOS/Linux 启动前端：

```bash
./scripts/start-frontend.sh
```

打开：

```text
http://127.0.0.1:5173
```

## 代理设置

网页中提供代理设置，默认是：

```text
http://127.0.0.1:7890
```

启用后会用于 YouTube 下载、Google 翻译、Edge-TTS 和 OpenAI 兼容 API 请求。

## OpenAI 兼容翻译

在页面中展开设置，选择：

```text
ChatGPT / OpenAI 兼容 API
```

然后填写：

- API Key
- Base URL，例如 `https://api.openai.com/v1`
- 模型，例如 `gpt-4o-mini`

API Key 只保存在你本机浏览器的 localStorage 中。

## 输出文件

每个任务会写入：

```text
workspace/jobs/{job_id}/
```

常见产物包括：

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

翻译缓存位于：

```text
workspace/translation-cache/
```

## 注意事项

- 硬字幕需要重新编码视频，可以通过 CRF 和 preset 平衡文件大小、速度和画质。
- 本地 TTS 音色取决于系统安装了哪些语音。跨平台场景建议优先使用 Edge-TTS。
- Edge-TTS 在某些语音或网络环境下可能不稳定，需要时可使用本地 TTS 兜底。
- Faster-Whisper 首次使用模型时会自动下载。
