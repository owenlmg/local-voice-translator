$ErrorActionPreference = "Continue"

$ports = @(5173, 8000)
foreach ($port in $ports) {
  $connections = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue
  foreach ($connection in $connections) {
    $pidValue = $connection.OwningProcess
    if ($pidValue) {
      Get-Process -Id $pidValue -ErrorAction SilentlyContinue | Stop-Process -Force
      Write-Host "Stopped process $pidValue on port $port"
    }
  }
}

Get-Process ffmpeg -ErrorAction SilentlyContinue | Stop-Process -Force
Write-Host "Stopped local services."

