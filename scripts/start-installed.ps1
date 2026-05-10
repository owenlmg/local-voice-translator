$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

$localFfmpegBin = Join-Path $root "tools\ffmpeg\bin"
if (Test-Path $localFfmpegBin) {
  $env:PATH = "$localFfmpegBin;$env:PATH"
}

if (-not (Get-Command ffmpeg -ErrorAction SilentlyContinue) -or -not (Get-Command ffprobe -ErrorAction SilentlyContinue)) {
  Write-Host "ffmpeg/ffprobe were not found. The installer should include tools\ffmpeg.zip, or install FFmpeg globally." -ForegroundColor Red
  exit 1
}

$proxyReady = Test-NetConnection 127.0.0.1 -Port 7890 -InformationLevel Quiet
if ($proxyReady) {
  $env:HTTP_PROXY = "http://127.0.0.1:7890"
  $env:HTTPS_PROXY = "http://127.0.0.1:7890"
  $env:ALL_PROXY = "http://127.0.0.1:7890"
  Write-Host "Proxy detected: http://127.0.0.1:7890"
}

$portablePython = Join-Path $root "python-runtime\python.exe"
if (Test-Path $portablePython) {
  $python = $portablePython
  $sitePackages = Join-Path $root "python-runtime\Lib\site-packages"
  if (Test-Path $sitePackages) {
    $env:PYTHONPATH = "$sitePackages;$root"
  } else {
    $env:PYTHONPATH = $root
  }
  Write-Host "Using bundled Python runtime."
} elseif (Test-Path ".venv\Scripts\python.exe") {
  $python = Join-Path $root ".venv\Scripts\python.exe"
} else {
  $systemPython = Get-Command python -ErrorAction SilentlyContinue
  if ($null -eq $systemPython -or $systemPython.Source -like "*WindowsApps*") {
    $systemPython = Get-Command py -ErrorAction SilentlyContinue
  }
  if ($null -eq $systemPython) {
    Write-Host "Python 3.10+ was not found. Install Python first, then run LocalVoiceProSetup.exe again." -ForegroundColor Red
    Write-Host "Download: https://www.python.org/downloads/windows/"
    exit 1
  }
  Write-Host "Creating Python virtual environment..."
  & $systemPython.Source -m venv .venv
  $python = Join-Path $root ".venv\Scripts\python.exe"
}

if (-not (Test-Path $portablePython)) {
  Write-Host "Installing backend dependencies..."
  & $python -m pip install --upgrade pip
  & $python -m pip install -r backend\requirements.txt
}

$frontendDist = Join-Path $root "frontend\dist\index.html"
if (-not (Test-Path $frontendDist)) {
  Write-Host "frontend\dist was not found. Build the frontend before packaging." -ForegroundColor Red
  exit 1
}

$workspace = Join-Path $root "workspace"
New-Item -ItemType Directory -Force -Path $workspace | Out-Null
$pidFile = Join-Path $workspace "local-voice-pro-installed.pid"
$stdoutLog = Join-Path $workspace "backend-installed.out.log"
$stderrLog = Join-Path $workspace "backend-installed.err.log"

Write-Host "Starting Local Voice Pro..."
$backend = Start-Process -FilePath $python -ArgumentList @("-m", "uvicorn", "backend.app.main:app", "--host", "127.0.0.1", "--port", "8000") -WorkingDirectory $root -WindowStyle Hidden -RedirectStandardOutput $stdoutLog -RedirectStandardError $stderrLog -PassThru
$backend.Id | Set-Content -Path $pidFile

Start-Sleep -Seconds 4

Write-Host ""
Write-Host "Local Voice Pro is running." -ForegroundColor Green
Write-Host "Open: http://127.0.0.1:8000"
Write-Host "Backend PID: $($backend.Id)"
Write-Host "Logs:"
Write-Host "  $stdoutLog"
Write-Host "  $stderrLog"
Write-Host ""
Write-Host "Run stop.bat or scripts\stop-all.ps1 to stop services."

Start-Process "http://127.0.0.1:8000"
