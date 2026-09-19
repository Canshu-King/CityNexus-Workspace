$ErrorActionPreference = 'Stop'
$calibration = 'D:\moodle\CityNexus\visio-renderer\calibration'
$outputRoot = Join-Path $calibration 'out\quota_joint_20260908'
$fixedRoutes = Join-Path $outputRoot 'P1_PARTIAL15C_FIXED_ROUTES.yaml'
$workerCount = 24

New-Item -ItemType Directory -Force -Path $outputRoot | Out-Null
$processes = @()
foreach ($index in 0..($workerCount - 1)) {
    $resultFile = Join-Path $outputRoot ("eight-shard-{0}.json" -f ($index + 1))
    $logFile = Join-Path $outputRoot ("eight-shard-{0}.log" -f ($index + 1))
    $errorFile = "$logFile.err"
    Remove-Item -LiteralPath $resultFile, $logFile, $errorFile -Force -ErrorAction SilentlyContinue
    $arguments = @(
        'search_quota_cluster_ports.py',
        '--fixed-routes', $fixedRoutes,
        '--shard-index', [string]$index,
        '--shard-count', [string]$workerCount,
        '--route-samples', '84',
        '--port-samples', '12',
        '--pair-samples', '4',
        '--independent-pa',
        '--include-candidates',
        '--export-only',
        '--max-b06-candidates', '240',
        '--seconds', '720',
        '--seed', [string](2026090800 + $index * 104729),
        '--json-out', $resultFile
    )
    $processes += Start-Process -FilePath 'python' -ArgumentList $arguments `
        -WorkingDirectory $calibration -RedirectStandardOutput $logFile `
        -RedirectStandardError $errorFile -WindowStyle Hidden -PassThru
}
$processes | Select-Object Id, StartTime | Format-Table -AutoSize
$processes.Id | Set-Content -LiteralPath (Join-Path $outputRoot 'eight-pids.txt')
