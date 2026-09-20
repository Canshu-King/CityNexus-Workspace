param(
  [Parameter(Mandatory = $true)] [string]$ConfigPath,
  [Parameter(Mandatory = $true)] [string]$PublicHost,
  [string]$Cloudflared = "cloudflared",
  [string]$PidFile = "run\\citynexus_preview_tunnel.pid",
  [string]$EndpointFile = "run\\preview_endpoint.txt"
)

$ErrorActionPreference = "Stop"

if ($PublicHost -match "trycloudflare\\.com$") { throw "Quick-tunnel hostnames are not accepted for the fixed preview." }
if (-not (Test-Path -LiteralPath $ConfigPath)) { throw "Tunnel config not found: $ConfigPath" }

$configText = Get-Content -LiteralPath $ConfigPath -Raw
if ($configText -notmatch "(?m)^tunnel:\\s*\\S+" -or $configText -notmatch "(?m)^credentials-file:\\s*\\S+" -or $configText -notmatch [regex]::Escape("hostname: $PublicHost")) {
  throw "Tunnel config must contain tunnel, credentials-file, and hostname: $PublicHost"
}

$pidParent = Split-Path -Parent $PidFile
if ($pidParent) { New-Item -ItemType Directory -Force -Path $pidParent | Out-Null }
$endpointParent = Split-Path -Parent $EndpointFile
if ($endpointParent) { New-Item -ItemType Directory -Force -Path $endpointParent | Out-Null }

if (Test-Path -LiteralPath $PidFile) {
  $existingPidText = (Get-Content -LiteralPath $PidFile -Raw).Trim()
  if ($existingPidText -match "^\\d+$") {
    $existing = Get-Process -Id ([int]$existingPidText) -ErrorAction SilentlyContinue
    if ($existing -and $existing.ProcessName -like "cloudflared*") {
      throw "Preview tunnel is already running as PID $existingPidText. Stop it explicitly before starting another."
    }
  }
  Remove-Item -LiteralPath $PidFile -Force
}

$process = Start-Process -FilePath $Cloudflared -ArgumentList @("--config", $ConfigPath, "tunnel", "run") -PassThru -WindowStyle Hidden
Start-Sleep -Seconds 2
$running = Get-Process -Id $process.Id -ErrorAction SilentlyContinue
if (-not $running) { throw "cloudflared exited during startup. Inspect its local log/config." }

Set-Content -LiteralPath $PidFile -Value ([string]$process.Id) -NoNewline
Set-Content -LiteralPath $EndpointFile -Value ("https://" + $PublicHost) -NoNewline
Write-Host ("CityNexus named tunnel started. PID={0} endpoint=https://{1}" -f $process.Id, $PublicHost)
