$ErrorActionPreference = 'Stop'
$calibration = 'D:\moodle\CityNexus\visio-renderer\calibration'
$outputRoot = Join-Path $calibration 'out\quota_joint_20260908'
$fixedRoutes = Join-Path $outputRoot 'fast8-4-fixed14.yaml'
$overrides = Join-Path $outputRoot 'fast8-4-overrides.yaml'
$processes = @()
foreach ($index in 0..23) {
    $number = $index + 1
    $resultFile = Join-Path $outputRoot ("four-hard-{0}.json" -f $number)
    $logFile = Join-Path $outputRoot ("four-hard-{0}.log" -f $number)
    $errorFile = "$logFile.err"
    Remove-Item -LiteralPath $resultFile, $logFile, $errorFile -Force -ErrorAction SilentlyContinue
    $arguments = @(
        'search_near_four_hard.py',
        '--fixed-routes', $fixedRoutes,
        '--route-overrides', $overrides,
        '--trials', '5000',
        '--seed', [string](5026090800 + $index * 1701149),
        '--json-out', $resultFile
    )
    $processes += Start-Process -FilePath 'python' -ArgumentList $arguments `
        -WorkingDirectory $calibration -RedirectStandardOutput $logFile `
        -RedirectStandardError $errorFile -WindowStyle Hidden -PassThru
}
$processes | Select-Object Id, StartTime | Format-Table -AutoSize
$processes.Id | Set-Content -LiteralPath (Join-Path $outputRoot 'four-hard-pids.txt')
