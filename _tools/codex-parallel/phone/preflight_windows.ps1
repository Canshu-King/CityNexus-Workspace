[CmdletBinding()]
param(
    [int]$BackendPort = 8000,
    [int]$FrontendPort = 5173,
    [string]$BackendHealthUrl = 'http://127.0.0.1:8000/api/v1/health',
    [string]$FrontendUrl = 'http://127.0.0.1:5173/v8',
    [string]$OutputDirectory = (Join-Path $PSScriptRoot 'out')
)
$ErrorActionPreference = 'Stop'
$allowedRoot = [System.IO.Path]::GetFullPath((Split-Path $PSScriptRoot -Parent))
$resolvedOutput = [System.IO.Path]::GetFullPath($OutputDirectory)
if (-not $resolvedOutput.StartsWith($allowedRoot, [System.StringComparison]::OrdinalIgnoreCase)) {
    throw "OutputDirectory must stay under $allowedRoot"
}
New-Item -ItemType Directory -Force -Path $resolvedOutput | Out-Null
$ips = Get-NetIPAddress -AddressFamily IPv4 -ErrorAction SilentlyContinue |
    Where-Object { $_.IPAddress -notlike '127.*' -and $_.IPAddress -notlike '169.254.*' } |
    Select-Object InterfaceAlias,IPAddress,PrefixLength
$listeners = Get-NetTCPConnection -State Listen -ErrorAction SilentlyContinue |
    Where-Object { $_.LocalPort -in @($BackendPort,$FrontendPort) } |
    Select-Object LocalAddress,LocalPort,OwningProcess
try { $health = Invoke-RestMethod -Uri $BackendHealthUrl -Method Get -TimeoutSec 5 } catch { $health = @{ error = $_.Exception.Message } }
$phoneUrls = foreach($ip in $ips.IPAddress){ "http://${ip}:$FrontendPort/v8" }
$result = [ordered]@{
    captured_at = (Get-Date).ToUniversalTime().ToString('o')
    computer = $env:COMPUTERNAME
    powershell = $PSVersionTable.PSVersion.ToString()
    backend_port = $BackendPort
    frontend_port = $FrontendPort
    addresses = @($ips)
    listeners = @($listeners)
    backend_health = $health
    local_frontend_url = $FrontendUrl
    phone_candidate_urls = @($phoneUrls)
    firewall_changed = $false
    adb_changed = $false
}
$path = Join-Path $resolvedOutput 'windows-preflight.json'
$result | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $path -Encoding utf8
$result | ConvertTo-Json -Depth 8
Write-Host "Saved: $path"
