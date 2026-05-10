$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

$localFfmpegBin = Join-Path $root "tools\ffmpeg\bin"
if (Test-Path $localFfmpegBin) {
  $env:PATH = "$localFfmpegBin;$env:PATH"
}

if (-not $env:HTTP_PROXY -and (Test-NetConnection 127.0.0.1 -Port 7890 -InformationLevel Quiet)) {
  $env:HTTP_PROXY = "http://127.0.0.1:7890"
  $env:HTTPS_PROXY = "http://127.0.0.1:7890"
}
if ($env:HTTP_PROXY -eq "http://127.0.0.1:7890" -or (Test-NetConnection 127.0.0.1 -Port 7890 -InformationLevel Quiet)) {
  $env:HTTP_PROXY = "http://127.0.0.1:7890"
  $env:HTTPS_PROXY = "http://127.0.0.1:7890"
  $env:ALL_PROXY = "http://127.0.0.1:7890"
}

if (Test-Path ".venv\Scripts\python.exe") {
  $python = ".venv\Scripts\python.exe"
} else {
  $python = "python"
}

& $python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
