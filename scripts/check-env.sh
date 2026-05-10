#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOCAL_FFMPEG_BIN="$ROOT_DIR/tools/ffmpeg/bin"

if [[ -d "$LOCAL_FFMPEG_BIN" ]]; then
  export PATH="$LOCAL_FFMPEG_BIN:$PATH"
fi

check_command() {
  local name="$1"
  if command -v "$name" >/dev/null 2>&1; then
    echo "[ok] $name: $(command -v "$name")"
    "$name" --version 2>/dev/null | head -n 1 || true
  else
    echo "[missing] $name was not found in PATH"
    return 1
  fi
}

echo "Checking Local Voice Pro environment..."
echo "Root: $ROOT_DIR"
echo "OS: $(uname -s)"
echo ""

check_command python3 || check_command python || true
check_command node || true
check_command npm || true
check_command ffmpeg || true
check_command ffprobe || true

echo ""
PYTHON_FOR_CHECK=""
if command -v python3 >/dev/null 2>&1; then
  PYTHON_FOR_CHECK="$(command -v python3)"
elif command -v python >/dev/null 2>&1; then
  PYTHON_FOR_CHECK="$(command -v python)"
fi

if [[ -n "$PYTHON_FOR_CHECK" ]] && "$PYTHON_FOR_CHECK" - <<'PY' >/dev/null 2>&1
import socket
with socket.create_connection(("127.0.0.1", 7890), timeout=0.4):
    pass
PY
then
  echo "[ok] proxy detected: http://127.0.0.1:7890"
else
  echo "[info] default proxy http://127.0.0.1:7890 is not reachable"
fi
