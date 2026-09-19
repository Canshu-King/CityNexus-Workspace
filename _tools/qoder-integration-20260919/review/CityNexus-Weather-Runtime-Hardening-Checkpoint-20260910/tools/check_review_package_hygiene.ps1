param(
    [Parameter(Mandatory=$true)]
    [string]$Root
)

$ErrorActionPreference = "Stop"
$forbidden = Get-ChildItem -LiteralPath $Root -Recurse -Force | Where-Object {
    $_.FullName -match "(\\|/)(\.venv|node_modules|dist|\.pytest_cache|\.ruff_cache|__pycache__|test-results)(\\|/|$)" -or
    $_.Name -match "\.pyc$" -or
    $_.Name -match "\.(db|sqlite|sqlite3)$"
}

if ($forbidden) {
    Write-Host "Review package hygiene FAIL"
    $forbidden | ForEach-Object { Write-Host $_.FullName }
    exit 1
}

Write-Host "Review package hygiene PASS"
