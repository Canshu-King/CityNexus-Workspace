param([string]$PidFile = "run\\citynexus_preview_tunnel.pid")
$ErrorActionPreference = "Stop"

if (-not (Test-Path -LiteralPath $PidFile)) { Write-Host "No recorded CityNexus preview tunnel PID."; exit 0 }
$pidText = (Get-Content -LiteralPath $PidFile -Raw).Trim()
if ($pidText -notmatch "^\\d+$") { throw "Invalid PID file: $PidFile" }

$process = Get-Process -Id ([int]$pidText) -ErrorAction SilentlyContinue
if ($process) {
  if ($process.ProcessName -notlike "cloudflared*") { throw "Recorded PID $pidText is not cloudflared; refusing to stop an unrelated process." }
  Stop-Process -Id $process.Id -ErrorAction Stop
  $process.WaitForExit()
}
Remove-Item -LiteralPath $PidFile -Force
Write-Host "CityNexus preview tunnel stopped."
