$ErrorActionPreference = "Continue"

Write-Host "Checking local toolchain..."

$root = Split-Path -Parent $PSScriptRoot
$localFfmpegBin = Join-Path $root "tools\ffmpeg\bin"
if (Test-Path $localFfmpegBin) {
  $env:PATH = "$localFfmpegBin;$env:PATH"
}

$python = Get-Command python -ErrorAction SilentlyContinue
if ($null -eq $python) {
  Write-Host "[missing] python was not found in PATH" -ForegroundColor Red
} elseif ($python.Source -like "*WindowsApps*") {
  Write-Host "[warning] python points to the WindowsApps launcher placeholder: $($python.Source)" -ForegroundColor Yellow
  Write-Host "          Install Python 3.10/3.11 and make sure the real python.exe appears earlier in PATH."
} else {
  Write-Host "[ok] python: $($python.Source)" -ForegroundColor Green
  python --version
}

$node = Get-Command node -ErrorAction SilentlyContinue
if ($null -eq $node) {
  Write-Host "[missing] node was not found in PATH" -ForegroundColor Red
} else {
  Write-Host "[ok] node: $($node.Source)" -ForegroundColor Green
  node --version
}

$npm = Get-Command npm.cmd -ErrorAction SilentlyContinue
if ($null -eq $npm) {
  Write-Host "[missing] npm.cmd was not found in PATH" -ForegroundColor Red
} else {
  Write-Host "[ok] npm.cmd: $($npm.Source)" -ForegroundColor Green
  npm.cmd --version
}

$ffmpeg = Get-Command ffmpeg -ErrorAction SilentlyContinue
$ffprobe = Get-Command ffprobe -ErrorAction SilentlyContinue
if ($null -eq $ffmpeg -or $null -eq $ffprobe) {
  Write-Host "[missing] ffmpeg/ffprobe were not found in PATH" -ForegroundColor Red
  Write-Host "          Install ffmpeg globally, or place it at tools\ffmpeg\bin."
} else {
  Write-Host "[ok] ffmpeg: $($ffmpeg.Source)" -ForegroundColor Green
  ffmpeg -version | Select-Object -First 1
}
