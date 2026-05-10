from enum import Enum
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field


class JobStatus(str, Enum):
    queued = "queued"
    running = "running"
    completed = "completed"
    failed = "failed"
    cancelled = "cancelled"


class JobOptions(BaseModel):
    pipeline_step: str = "dub"
    source_language: str = "auto"
    target_language: str = "zh-CN"
    translation_provider: str = "google"
    openai_api_key: str = ""
    openai_base_url: str = "https://api.openai.com/v1"
    openai_model: str = "gpt-4o-mini"
    force_retranslate: bool = False
    whisper_model: str = "base"
    tts_voice: str = "zh-CN-XiaoxiaoNeural"
    tts_engine: str = "auto"
    tts_rate: int = 0
    tts_pitch: int = 0
    tts_volume: int = 0
    proxy_enabled: bool = True
    proxy_url: str = "http://127.0.0.1:7890"
    caption_preset: str = "medium"
    caption_crf: int = 28


class Artifact(BaseModel):
    key: str
    label: str
    kind: str
    path: str
    size: int = 0


class JobManifest(BaseModel):
    id: str
    status: JobStatus = JobStatus.queued
    progress: int = 0
    stage: str = "Queued"
    options: JobOptions = Field(default_factory=JobOptions)
    source_type: str = "upload"
    source_url: str | None = None
    input_name: str
    input_path: str = ""
    has_video: bool = False
    has_audio: bool = False
    logs: list[str] = Field(default_factory=list)
    artifacts: list[Artifact] = Field(default_factory=list)
    error: str | None = None
    cancel_requested: bool = False

    def add_log(self, message: str) -> None:
        self.logs.append(message)

    def set_stage(self, stage: str, progress: int) -> None:
        self.stage = stage
        self.progress = max(0, min(100, progress))

    def upsert_artifact(self, key: str, label: str, kind: str, path: Path) -> None:
        path_str = str(path)
        artifact = Artifact(
            key=key,
            label=label,
            kind=kind,
            path=path_str,
            size=path.stat().st_size if path.exists() else 0,
        )
        self.artifacts = [item for item in self.artifacts if item.key != key]
        self.artifacts.append(artifact)

    def public_dict(self) -> dict[str, Any]:
        data = self.model_dump()
        options = data.get("options", {})
        if options.get("openai_api_key"):
            options["openai_api_key"] = "********"
        return data
