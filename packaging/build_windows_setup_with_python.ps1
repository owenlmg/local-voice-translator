$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
$payloadDir = Join-Path $root "build\windows-payload-with-python"
$payloadZip = Join-Path $root "build\payload-with-python.zip"
$distDir = Join-Path $root "dist"
$python = Join-Path $root ".venv\Scripts\python.exe"

function Invoke-Robocopy {
  param(
    [Parameter(Mandatory = $true)][string]$Source,
    [Parameter(Mandatory = $true)][string]$Destination,
    [string[]]$ExtraArgs = @()
  )
  New-Item -ItemType Directory -Force -Path $Destination | Out-Null
  & robocopy $Source $Destination /E /NFL /NDL /NJH /NJS /NP @ExtraArgs | Out-Null
  if ($LASTEXITCODE -ge 8) {
    throw "robocopy failed from $Source to $Destination with exit code $LASTEXITCODE"
  }
}

if (-not (Test-Path $python)) {
  throw "Project virtual environment was not found at .venv\Scripts\python.exe"
}

Set-Location $root

Write-Host "Building frontend..."
Push-Location frontend
npm.cmd run build
Pop-Location

if (Test-Path $payloadDir) {
  Remove-Item -Recurse -Force $payloadDir
}
if (Test-Path $payloadZip) {
  Remove-Item -Force $payloadZip
}
New-Item -ItemType Directory -Force -Path $payloadDir | Out-Null

$items = @(
  "backend",
  "frontend\dist",
  "scripts",
  "README.md",
  "README.zh-CN.md",
  "start.bat",
  "stop.bat"
)

foreach ($item in $items) {
  $source = Join-Path $root $item
  $destination = Join-Path $payloadDir $item
  if (Test-Path $source -PathType Container) {
    New-Item -ItemType Directory -Force -Path (Split-Path -Parent $destination) | Out-Null
    Copy-Item -Recurse -Force $source $destination
  } else {
    New-Item -ItemType Directory -Force -Path (Split-Path -Parent $destination) | Out-Null
    Copy-Item -Force $source $destination
  }
}

$ffmpegZip = Join-Path $root "tools\ffmpeg.zip"
if (Test-Path $ffmpegZip) {
  New-Item -ItemType Directory -Force -Path (Join-Path $payloadDir "tools") | Out-Null
  Copy-Item -Force $ffmpegZip (Join-Path $payloadDir "tools\ffmpeg.zip")
}

Write-Host "Preparing bundled Python runtime..."
$pythonInfo = & $python -c "import json, sys; print(json.dumps({'base': sys.base_prefix, 'site': next(p for p in sys.path if p.endswith('site-packages'))}))" | ConvertFrom-Json
$runtimeDir = Join-Path $payloadDir "python-runtime"
Invoke-Robocopy -Source $pythonInfo.base -Destination $runtimeDir -ExtraArgs @(
  "/XD", "__pycache__", "Scripts", "include", "libs", "tcl\test", "Lib\test", "Lib\idlelib", "Lib\tkinter",
  "/XF", "*.pyc", "*.pyo"
)

$runtimeSite = Join-Path $runtimeDir "Lib\site-packages"
Invoke-Robocopy -Source $pythonInfo.site -Destination $runtimeSite -ExtraArgs @(
  "/XD", "__pycache__", "PyInstaller", "PyInstaller-*.dist-info", "_pyinstaller_hooks_contrib", "pyinstaller_hooks_contrib-*.dist-info", "altgraph", "altgraph-*.dist-info", "pefile-*.dist-info", "pywin32_ctypes-*.dist-info",
  "/XF", "*.pyc", "*.pyo"
)

Write-Host "Smoke testing bundled Python runtime..."
& (Join-Path $runtimeDir "python.exe") -c "import fastapi, uvicorn, faster_whisper, edge_tts, yt_dlp; print('bundled python ok')"

Write-Host "Creating payload zip..."
Compress-Archive -Path (Join-Path $payloadDir "*") -DestinationPath $payloadZip -Force

Write-Host "Installing PyInstaller if needed..."
& $python -m pip install --upgrade pyinstaller

Write-Host "Building LocalVoiceProSetup-WithPython.exe..."
New-Item -ItemType Directory -Force -Path $distDir | Out-Null
& $python -m PyInstaller `
  --noconfirm `
  --clean `
  --onefile `
  --console `
  --name LocalVoiceProSetup-WithPython `
  --add-data "$payloadZip;." `
  --distpath $distDir `
  --workpath (Join-Path $root "build\pyinstaller-with-python") `
  --specpath (Join-Path $root "build") `
  (Join-Path $root "packaging\windows_launcher.py")

Write-Host ""
Write-Host "Built: $(Join-Path $distDir 'LocalVoiceProSetup-WithPython.exe')"
