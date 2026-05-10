#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

LOCAL_FFMPEG_BIN="$ROOT_DIR/tools/ffmpeg/bin"
if [[ -d "$LOCAL_FFMPEG_BIN" ]]; then
  export PATH="$LOCAL_FFMPEG_BIN:$PATH"
fi

if ! command -v ffmpeg >/dev/null 2>&1 || ! command -v ffprobe >/dev/null 2>&1; then
  echo "ffmpeg/ffprobe were not found. Install FFmpeg first, or place binaries in tools/ffmpeg/bin." >&2
  echo "macOS: brew install ffmpeg" >&2
  echo "Ubuntu/Debian: sudo apt update && sudo apt install -y ffmpeg" >&2
  exit 1
fi

if [[ -x ".venv/bin/python" ]]; then
  PYTHON=".venv/bin/python"
else
  if command -v python3 >/dev/null 2>&1; then
    SYSTEM_PYTHON="$(command -v python3)"
  elif command -v python >/dev/null 2>&1; then
    SYSTEM_PYTHON="$(command -v python)"
  else
    echo "Python 3.10+ was not found in PATH." >&2
    exit 1
  fi

  echo "Creating Python virtual environment..."
  "$SYSTEM_PYTHON" -m venv .venv
  PYTHON=".venv/bin/python"
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
  echo "Proxy detected: http://127.0.0.1:7890"
fi

echo "Installing backend dependencies..."
"$PYTHON" -m pip install --upgrade pip
"$PYTHON" -m pip install -r backend/requirements.txt

if ! command -v npm >/dev/null 2>&1; then
  echo "npm was not found. Install Node.js first." >&2
  exit 1
fi

if [[ ! -d "frontend/node_modules" ]]; then
  echo "Installing frontend dependencies..."
  (cd frontend && npm install)
fi

mkdir -p workspace

BACKEND_LOG="$ROOT_DIR/workspace/backend.log"
FRONTEND_LOG="$ROOT_DIR/workspace/frontend.log"
PID_FILE="$ROOT_DIR/workspace/local-voice-pro.pids"

echo "Starting backend..."
"$PYTHON" -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 >"$BACKEND_LOG" 2>&1 &
BACKEND_PID=$!

echo "Starting frontend..."
(cd frontend && npm run dev -- --host 127.0.0.1 >"$FRONTEND_LOG" 2>&1) &
FRONTEND_PID=$!

printf "%s\n%s\n" "$BACKEND_PID" "$FRONTEND_PID" > "$PID_FILE"

sleep 4

echo ""
echo "Local Voice Pro is running."
echo "Frontend: http://127.0.0.1:5173"
echo "Backend:  http://127.0.0.1:8000"
echo "Backend PID:  $BACKEND_PID"
echo "Frontend PID: $FRONTEND_PID"
echo "Logs:"
echo "  $BACKEND_LOG"
echo "  $FRONTEND_LOG"
echo ""
echo "Run ./stop.sh to stop services."

if command -v open >/dev/null 2>&1; then
  open "http://127.0.0.1:5173" >/dev/null 2>&1 || true
elif command -v xdg-open >/dev/null 2>&1; then
  xdg-open "http://127.0.0.1:5173" >/dev/null 2>&1 || true
fi
