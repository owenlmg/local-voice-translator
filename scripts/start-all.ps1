$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

$localFfmpegBin = Join-Path $root "tools\ffmpeg\bin"
if (Test-Path $localFfmpegBin) {
  $env:PATH = "$localFfmpegBin;$env:PATH"
}

if (-not (Get-Command ffmpeg -ErrorAction SilentlyContinue)) {
  Write-Host "ffmpeg was not found. Expected tools\ffmpeg\bin\ffmpeg.exe or ffmpeg in PATH." -ForegroundColor Red
  exit 1
}

$proxyReady = Test-NetConnection 127.0.0.1 -Port 7890 -InformationLevel Quiet
if ($proxyReady) {
  $env:HTTP_PROXY = "http://127.0.0.1:7890"
  $env:HTTPS_PROXY = "http://127.0.0.1:7890"
  $env:ALL_PROXY = "http://127.0.0.1:7890"
  Write-Host "Proxy detected: http://127.0.0.1:7890"
}

if (Test-Path ".venv\Scripts\python.exe") {
  $python = Join-Path $root ".venv\Scripts\python.exe"
} else {
  $systemPython = Get-Command python -ErrorAction SilentlyContinue
  if ($null -eq $systemPython -or $systemPython.Source -like "*WindowsApps*") {
    Write-Host "A real Python installation was not found in PATH. Install Python 3.10+ first." -ForegroundColor Red
    exit 1
  }
  Write-Host "Creating Python virtual environment..."
  & $systemPython.Source -m venv .venv
  $python = Join-Path $root ".venv\Scripts\python.exe"
}

Write-Host "Installing backend dependencies..."
& $python -m pip install --upgrade pip
& $python -m pip install -r backend\requirements.txt

if (-not (Get-Command npm.cmd -ErrorAction SilentlyContinue)) {
  Write-Host "npm.cmd was not found. Install Node.js first." -ForegroundColor Red
  exit 1
}

if (-not (Test-Path "frontend\node_modules")) {
  Write-Host "Installing frontend dependencies..."
  Push-Location frontend
  npm.cmd install
  Pop-Location
}

Write-Host "Starting backend..."
$backend = Start-Process -FilePath $python -ArgumentList @("-m", "uvicorn", "backend.app.main:app", "--host", "127.0.0.1", "--port", "8000") -WorkingDirectory $root -WindowStyle Hidden -PassThru

Write-Host "Starting frontend..."
$frontendDir = Join-Path $root "frontend"
$frontend = Start-Process -FilePath "npm.cmd" -ArgumentList @("run", "dev", "--", "--host", "127.0.0.1") -WorkingDirectory $frontendDir -WindowStyle Hidden -PassThru

Start-Sleep -Seconds 4

Write-Host ""
Write-Host "Voice Pro Local is running." -ForegroundColor Green
Write-Host "Frontend: http://127.0.0.1:5173"
Write-Host "Backend:  http://127.0.0.1:8000"
Write-Host "Backend PID:  $($backend.Id)"
Write-Host "Frontend PID: $($frontend.Id)"
Write-Host ""
Write-Host "Close this window after you are done, or run scripts\stop-all.ps1 to stop services."

Start-Process "http://127.0.0.1:5173"

