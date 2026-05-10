#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

LOCAL_FFMPEG_BIN="$ROOT_DIR/tools/ffmpeg/bin"
if [[ -d "$LOCAL_FFMPEG_BIN" ]]; then
  export PATH="$LOCAL_FFMPEG_BIN:$PATH"
fi

if [[ -x ".venv/bin/python" ]]; then
  PYTHON=".venv/bin/python"
elif command -v python3 >/dev/null 2>&1; then
  PYTHON="$(command -v python3)"
else
  PYTHON="$(command -v python)"
fi

if "$PYTHON" - <<'PY' >/dev/null 2>&1
import socket
with socket.create_connection(("127.0.0.1", 7890), timeout=0.4):
    pass
PY
then
  export HTTP_PROXY="${HTTP_PROXY:-http://127.0.0.1:7890}"
  export HTTPS_PROXY="${HTTPS_PROXY:-http://127.0.0.1:7890}"
  export ALL_PROXY="${ALL_PROXY:-http://127.0.0.1:7890}"
fi

exec "$PYTHON" -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
