import json
from pathlib import Path

from .config import JOBS_DIR
from .models import JobManifest


def job_dir(job_id: str) -> Path:
    path = JOBS_DIR / job_id
    path.mkdir(parents=True, exist_ok=True)
    return path


def manifest_path(job_id: str) -> Path:
    return job_dir(job_id) / "manifest.json"


def save_manifest(manifest: JobManifest) -> None:
    path = manifest_path(manifest.id)
    path.write_text(
        json.dumps(manifest.model_dump(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def load_manifest(job_id: str) -> JobManifest:
    path = manifest_path(job_id)
    if not path.exists():
        raise FileNotFoundError(job_id)
    return JobManifest.model_validate_json(path.read_text(encoding="utf-8"))


def list_manifests() -> list[JobManifest]:
    manifests: list[JobManifest] = []
    for path in JOBS_DIR.glob("*/manifest.json"):
        try:
            manifests.append(JobManifest.model_validate_json(path.read_text(encoding="utf-8")))
        except Exception:
            continue
    return sorted(manifests, key=lambda item: item.id, reverse=True)

