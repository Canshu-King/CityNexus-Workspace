param([Parameter(Mandatory=$true)][string]$Root)
$ErrorActionPreference = "Stop"
$rootPath = Resolve-Path $Root
$bad = Get-ChildItem -LiteralPath $rootPath -Recurse -Force | Where-Object {
    $_.Name -eq '__pycache__' -or
    $_.Name -eq '.pytest_cache' -or
    $_.Name -eq 'node_modules' -or
    $_.Name -eq '.venv' -or
    $_.Name -eq 'dist' -or
    (!$_.PSIsContainer -and ($_.Extension -in @('.pyc','.pyo','.db','.sqlite','.sqlite3')))
}
if ($bad) {
    $bad | ForEach-Object { Write-Host $_.FullName }
    throw "Review package contains generated/runtime artifacts."
}
Write-Host "Review package hygiene PASS"
