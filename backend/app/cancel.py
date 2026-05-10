import subprocess
from threading import Lock

from .models import JobManifest, JobStatus
from .store import load_manifest, save_manifest


_LOCK = Lock()
_PROCESSES: dict[str, subprocess.Popen] = {}


class JobCancelled(RuntimeError):
    pass


def request_cancel(job_id: str) -> JobManifest:
    manifest = load_manifest(job_id)
    manifest.cancel_requested = True
    manifest.add_log("Cancel requested.")
    save_manifest(manifest)
    with _LOCK:
        process = _PROCESSES.get(job_id)
    if process and process.poll() is None:
        process.terminate()
    return manifest


def register_process(job_id: str, process: subprocess.Popen) -> None:
    with _LOCK:
        _PROCESSES[job_id] = process


def unregister_process(job_id: str, process: subprocess.Popen) -> None:
    with _LOCK:
        if _PROCESSES.get(job_id) is process:
            _PROCESSES.pop(job_id, None)


def check_cancelled(manifest: JobManifest) -> None:
    latest = load_manifest(manifest.id)
    manifest.cancel_requested = latest.cancel_requested
    if latest.cancel_requested:
        manifest.status = JobStatus.cancelled
        manifest.set_stage("Stopped", manifest.progress)
        manifest.add_log("Job stopped by user.")
        save_manifest(manifest)
        raise JobCancelled("Job stopped by user.")

