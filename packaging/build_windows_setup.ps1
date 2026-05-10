$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
$payloadDir = Join-Path $root "build\windows-payload"
$payloadZip = Join-Path $root "build\payload.zip"
$distDir = Join-Path $root "dist"
$python = Join-Path $root ".venv\Scripts\python.exe"

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

Write-Host "Creating payload zip..."
Compress-Archive -Path (Join-Path $payloadDir "*") -DestinationPath $payloadZip -Force

Write-Host "Installing PyInstaller if needed..."
& $python -m pip install --upgrade pyinstaller

Write-Host "Building LocalVoiceProSetup.exe..."
New-Item -ItemType Directory -Force -Path $distDir | Out-Null
& $python -m PyInstaller `
  --noconfirm `
  --clean `
  --onefile `
  --console `
  --name LocalVoiceProSetup `
  --add-data "$payloadZip;." `
  --distpath $distDir `
  --workpath (Join-Path $root "build\pyinstaller") `
  --specpath (Join-Path $root "build") `
  (Join-Path $root "packaging\windows_launcher.py")

Write-Host ""
Write-Host "Built: $(Join-Path $distDir 'LocalVoiceProSetup.exe')"
