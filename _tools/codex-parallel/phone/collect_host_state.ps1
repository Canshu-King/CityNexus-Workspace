[CmdletBinding()]
param(
    [string]$IntegrationPath = 'D:\moodle\_qoder_integration_20260919',
    [int[]]$Ports = @(8000,5173),
    [string]$OutputDirectory = (Join-Path $PSScriptRoot 'out')
)
$ErrorActionPreference = 'Stop'
$allowedRoot = [System.IO.Path]::GetFullPath((Split-Path $PSScriptRoot -Parent))
$resolvedOutput = [System.IO.Path]::GetFullPath($OutputDirectory)
if (-not $resolvedOutput.StartsWith($allowedRoot, [System.StringComparison]::OrdinalIgnoreCase)) {
    throw "OutputDirectory must stay under $allowedRoot"
}
New-Item -ItemType Directory -Force -Path $resolvedOutput | Out-Null
function GitValue([string[]]$Arguments) {
    try { return (& git -C $IntegrationPath @Arguments 2>$null | Out-String).Trim() } catch { return $null }
}
$statusLines = @(GitValue @('status','--short') -split "`r?`n" | Where-Object { $_ })
$state = [ordered]@{
    captured_at = (Get-Date).ToUniversalTime().ToString('o')
    os = [System.Environment]::OSVersion.VersionString
    powershell = $PSVersionTable.PSVersion.ToString()
    node = (& node --version 2>$null | Out-String).Trim()
    python = (& python --version 2>&1 | Out-String).Trim()
    integration = [ordered]@{
        path = $IntegrationPath
        head = GitValue @('rev-parse','HEAD')
        branch = GitValue @('rev-parse','--abbrev-ref','HEAD')
        dirty_count = $statusLines.Count
        dirty_paths = $statusLines
    }
    addresses = @(Get-NetIPAddress -AddressFamily IPv4 -ErrorAction SilentlyContinue |
        Where-Object { $_.IPAddress -notlike '127.*' -and $_.IPAddress -notlike '169.254.*' } |
        Select-Object InterfaceAlias,IPAddress,PrefixLength)
    listeners = @(Get-NetTCPConnection -State Listen -ErrorAction SilentlyContinue |
        Where-Object { $_.LocalPort -in $Ports } | Select-Object LocalAddress,LocalPort,OwningProcess)
    environment_names_only = @(Get-ChildItem Env: | Where-Object { $_.Name -like 'CITYNEXUS_*' } | Select-Object -ExpandProperty Name | Sort-Object)
}
$stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
$path = Join-Path $resolvedOutput "host-state-$stamp.json"
$state | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $path -Encoding utf8
Write-Host "Saved: $path"
$state | ConvertTo-Json -Depth 8
