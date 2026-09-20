param([string]$EndpointFile = "run\\preview_endpoint.txt")
$ErrorActionPreference = "Stop"

if (-not (Test-Path -LiteralPath $EndpointFile)) { throw "Preview endpoint file not found: $EndpointFile" }
$base = (Get-Content -LiteralPath $EndpointFile -Raw).TrimEnd("/")
if (-not $base.StartsWith("https://")) { throw "Preview endpoint must be https://" }

$paths = @("/api/v1/health", "/v8/live", "/manifest.webmanifest")
$failed = $false
foreach ($path in $paths) {
  $url = $base + $path
  $code = & curl.exe -sS -o NUL -w "%{http_code}" $url
  if ($LASTEXITCODE -ne 0) { Write-Host "$path transport_error"; $failed = $true; continue }
  Write-Host "$path anon=$code"
  if ($code -ne "401") { $failed = $true }
}
if ($failed) { throw "Preview health/security gate failed." }
Write-Host "Preview anonymous boundary is healthy."
