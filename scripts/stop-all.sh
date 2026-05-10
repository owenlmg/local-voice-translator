#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PID_FILE="$ROOT_DIR/workspace/local-voice-pro.pids"

if [[ -f "$PID_FILE" ]]; then
  while read -r pid; do
    if [[ -n "$pid" ]] && kill -0 "$pid" >/dev/null 2>&1; then
      kill "$pid" >/dev/null 2>&1 || true
      echo "Stopped process $pid"
    fi
  done < "$PID_FILE"
  rm -f "$PID_FILE"
fi

if command -v lsof >/dev/null 2>&1; then
  for port in 5173 8000; do
    pids="$(lsof -ti tcp:"$port" 2>/dev/null || true)"
    for pid in $pids; do
      kill "$pid" >/dev/null 2>&1 || true
      echo "Stopped process $pid on port $port"
    done
  done
fi

pkill -f "uvicorn backend.app.main:app" >/dev/null 2>&1 || true
pkill -f "vite.*127.0.0.1" >/dev/null 2>&1 || true
pkill -x ffmpeg >/dev/null 2>&1 || true

echo "Stopped local services."
