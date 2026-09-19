$ErrorActionPreference = 'Stop'
$calibration = 'D:\moodle\CityNexus\visio-renderer\calibration'
$outputRoot = Join-Path $calibration 'out\quota_joint_20260908'
$fixedRoutes = Join-Path $outputRoot 'P1_PARTIAL15C_FIXED_ROUTES.yaml'

New-Item -ItemType Directory -Force -Path $outputRoot | Out-Null
$processes = @()
foreach ($index in 1..12) {
    $seed = 202610300 + $index
    $shardIndex = [math]::Floor(($index - 1) / 2)
    $reroute = if (($index % 2) -eq 1) { 'A-M-UC-10' } else { 'A-CD-UC-10' }
    $resultFile = Join-Path $outputRoot ("union-triple-{0}.json" -f $index)
    $logFile = Join-Path $outputRoot ("union-triple-{0}.log" -f $index)
    $errorFile = "$logFile.err"
    Remove-Item -LiteralPath $resultFile, $logFile, $errorFile -Force -ErrorAction SilentlyContinue
    $arguments = @(
        'repair_uc10_triple_shard.py',
        '--input-pattern', (Join-Path $outputRoot 'union-*.json'),
        '--fixed-routes', $fixedRoutes,
        '--shard-index', [string]$shardIndex,
        '--shard-count', '6',
        '--reroute', $reroute,
        '--pair-limit', '120',
        '--samples', '12',
        '--seed', [string]$seed,
        '--json-out', $resultFile
    )
    $processes += Start-Process -FilePath 'python' -ArgumentList $arguments `
        -WorkingDirectory $calibration -RedirectStandardOutput $logFile `
        -RedirectStandardError $errorFile -WindowStyle Hidden -PassThru
}
$processes | Select-Object Id, StartTime | Format-Table -AutoSize
$processes.Id | Set-Content -LiteralPath (Join-Path $outputRoot 'pids.txt')
