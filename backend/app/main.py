from pathlib import Path
import shutil
import uuid

from fastapi import BackgroundTasks, FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from .cancel import request_cancel
from .config import JOBS_DIR, ROOT_DIR
from .models import JobManifest, JobOptions, JobStatus
from .pipeline.job_runner import continue_pipeline, render_caption_only, rerun_dubbing, run_full_pipeline
from .pipeline.media import require_ffmpeg
from .store import job_dir, list_manifests, load_manifest, save_manifest


app = FastAPI(title="Local Voice Pro MVP", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class SubtitleUpdate(BaseModel):
    content: str


class ContinueRequest(BaseModel):
    pipeline_step: str
    force_retranslate: bool = False
    translation_provider: str | None = None
    openai_api_key: str | None = None
    openai_base_url: str | None = None
    openai_model: str | None = None


@app.get("/api/health")
def health() -> dict:
    checks = {
        "python": True,
        "ffmpeg": True,
    }
    errors: list[str] = []
    try:
        require_ffmpeg()
    except Exception as exc:
        checks["ffmpeg"] = False
        errors.append(str(exc))
    return {"ok": all(checks.values()), "checks": checks, "errors": errors}


@app.get("/api/jobs")
def jobs() -> list[dict]:
    return [manifest.public_dict() for manifest in list_manifests()]


@app.post("/api/jobs")
async def create_job(
    background_tasks: BackgroundTasks,
    file: UploadFile | None = File(None),
    youtube_url: str = Form(""),
    pipeline_step: str = Form("dub"),
    source_language: str = Form("auto"),
    target_language: str = Form("zh-CN"),
    translation_provider: str = Form("google"),
    openai_api_key: str = Form(""),
    openai_base_url: str = Form("https://api.openai.com/v1"),
    openai_model: str = Form("gpt-4o-mini"),
    whisper_model: str = Form("base"),
    tts_voice: str = Form("zh-CN-XiaoxiaoNeural"),
    tts_engine: str = Form("auto"),
    tts_rate: int = Form(0),
    tts_pitch: int = Form(0),
    tts_volume: int = Form(0),
    proxy_enabled: bool = Form(True),
    proxy_url: str = Form("http://127.0.0.1:7890"),
    caption_preset: str = Form("medium"),
    caption_crf: int = Form(28),
) -> dict:
    if pipeline_step not in {"download", "subtitle", "translate", "caption", "dub"}:
        raise HTTPException(status_code=400, detail="Invalid pipeline step")
    if file is None and not youtube_url.strip():
        raise HTTPException(status_code=400, detail="Upload a file or provide a YouTube URL")

    job_id = uuid.uuid4().hex
    output_dir = job_dir(job_id)
    source_type = "youtube" if youtube_url.strip() else "upload"
    input_path = None
    if file is not None:
        safe_name = Path(file.filename or "upload.bin").name
        input_path = output_dir / safe_name
        with input_path.open("wb") as handle:
            shutil.copyfileobj(file.file, handle)
    else:
        safe_name = youtube_url.strip()

    manifest = JobManifest(
        id=job_id,
        status=JobStatus.queued,
        source_type=source_type,
        source_url=youtube_url.strip() or None,
        input_name=safe_name,
        input_path=str(input_path or ""),
        options=JobOptions(
            pipeline_step=pipeline_step,
            source_language=source_language,
            target_language=target_language,
            translation_provider=translation_provider,
            openai_api_key=openai_api_key,
            openai_base_url=openai_base_url,
            openai_model=openai_model,
            whisper_model=whisper_model,
            tts_voice=tts_voice,
            tts_engine=tts_engine,
            tts_rate=tts_rate,
            tts_pitch=tts_pitch,
            tts_volume=tts_volume,
            proxy_enabled=proxy_enabled,
            proxy_url=proxy_url,
            caption_preset=caption_preset,
            caption_crf=caption_crf,
        ),
    )
    if input_path is not None:
        manifest.upsert_artifact("source_media", "Source media", "media", input_path)
        manifest.add_log("Upload saved.")
    else:
        manifest.add_log("YouTube URL saved.")
    save_manifest(manifest)
    background_tasks.add_task(run_full_pipeline, manifest)
    return manifest.public_dict()


@app.get("/api/jobs/{job_id}")
def get_job(job_id: str) -> dict:
    try:
        return load_manifest(job_id).public_dict()
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Job not found")


@app.get("/api/jobs/{job_id}/artifacts")
def get_artifacts(job_id: str) -> list[dict]:
    try:
        return [item.model_dump() for item in load_manifest(job_id).artifacts]
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Job not found")


@app.get("/api/jobs/{job_id}/subtitles/{kind}")
def get_subtitle(job_id: str, kind: str) -> dict:
    if kind not in {"original", "translated"}:
        raise HTTPException(status_code=400, detail="kind must be original or translated")
    path = job_dir(job_id) / f"{kind}.srt"
    if not path.exists():
        raise HTTPException(status_code=404, detail="Subtitle not found")
    return {"kind": kind, "content": path.read_text(encoding="utf-8")}


@app.put("/api/jobs/{job_id}/subtitles/translated")
def update_translated_subtitle(job_id: str, payload: SubtitleUpdate) -> dict:
    try:
        manifest = load_manifest(job_id)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Job not found")
    path = job_dir(job_id) / "translated.srt"
    path.write_text(payload.content, encoding="utf-8")
    manifest.upsert_artifact("translated_srt", "Translated SRT", "subtitle", path)
    manifest.add_log("Translated subtitles edited.")
    save_manifest(manifest)
    return manifest.public_dict()


@app.post("/api/jobs/{job_id}/rerun-dubbing")
def rerun_job_dubbing(job_id: str, background_tasks: BackgroundTasks) -> dict:
    try:
        manifest = load_manifest(job_id)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Job not found")
    manifest.status = JobStatus.queued
    manifest.error = None
    manifest.add_log("Queued dubbing regeneration.")
    save_manifest(manifest)
    background_tasks.add_task(rerun_dubbing, manifest)
    return manifest.public_dict()


@app.post("/api/jobs/{job_id}/render-caption")
def render_job_caption(job_id: str, background_tasks: BackgroundTasks) -> dict:
    try:
        manifest = load_manifest(job_id)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Job not found")
    manifest.status = JobStatus.queued
    manifest.error = None
    manifest.add_log("Queued caption video rendering.")
    save_manifest(manifest)
    background_tasks.add_task(render_caption_only, manifest)
    return manifest.public_dict()


@app.post("/api/jobs/{job_id}/continue")
def continue_job(job_id: str, payload: ContinueRequest, background_tasks: BackgroundTasks) -> dict:
    if payload.pipeline_step not in {"subtitle", "translate", "caption", "dub"}:
        raise HTTPException(status_code=400, detail="Invalid continuation step")
    try:
        manifest = load_manifest(job_id)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Job not found")
    manifest.options.pipeline_step = payload.pipeline_step
    manifest.options.force_retranslate = payload.force_retranslate
    if payload.translation_provider:
        manifest.options.translation_provider = payload.translation_provider
    if payload.openai_api_key and payload.openai_api_key != "********":
        manifest.options.openai_api_key = payload.openai_api_key
    if payload.openai_base_url:
        manifest.options.openai_base_url = payload.openai_base_url
    if payload.openai_model:
        manifest.options.openai_model = payload.openai_model
    manifest.status = JobStatus.queued
    manifest.error = None
    manifest.add_log(f"Queued continuation to {payload.pipeline_step}.")
    save_manifest(manifest)
    background_tasks.add_task(continue_pipeline, manifest)
    return manifest.public_dict()


@app.post("/api/jobs/{job_id}/cancel")
def cancel_job(job_id: str) -> dict:
    try:
        manifest = request_cancel(job_id)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Job not found")
    return manifest.public_dict()


@app.get("/api/files/{file_path:path}")
def serve_file(file_path: str) -> FileResponse:
    candidate = Path(file_path)
    if not candidate.is_absolute():
        candidate = ROOT_DIR / candidate
    resolved = candidate.resolve()
    allowed = JOBS_DIR.resolve()
    if allowed not in resolved.parents and resolved != allowed:
        raise HTTPException(status_code=403, detail="File is outside workspace")
    if not resolved.exists() or not resolved.is_file():
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(resolved)


frontend_dist = ROOT_DIR / "frontend" / "dist"
if frontend_dist.exists():
    app.mount("/", StaticFiles(directory=frontend_dist, html=True), name="frontend")
