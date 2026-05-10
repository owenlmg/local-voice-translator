from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[2]
WORKSPACE_DIR = ROOT_DIR / "workspace"
JOBS_DIR = WORKSPACE_DIR / "jobs"
MAX_UPLOAD_BYTES = 4 * 1024 * 1024 * 1024


JOBS_DIR.mkdir(parents=True, exist_ok=True)

