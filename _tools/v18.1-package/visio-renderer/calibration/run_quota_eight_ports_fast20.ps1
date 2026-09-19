$ErrorActionPreference = 'Stop'
$calibration = 'D:\moodle\CityNexus\visio-renderer\calibration'
$outputRoot = Join-Path $calibration 'out\quota_joint_20260908'
$fixedRoutes = Join-Path $outputRoot 'P1_PARTIAL15C_FIXED_ROUTES.yaml'
$processes = @()
foreach ($index in 0..19) {
    $number = $index + 1
    $resultFile = Join-Path $outputRoot ("fast8-{0}.json" -f $number)
    $stagingFile = Join-Path $outputRoot ("fast8-{0}.yaml" -f $number)
    $logFile = Join-Path $outputRoot ("fast8-{0}.log" -f $number)
    $errorFile = "$logFile.err"
    Remove-Item -LiteralPath $resultFile, $stagingFile, $logFile, $errorFile -Force -ErrorAction SilentlyContinue
    $bendCosts = @(0.10, 0.25, 0.50)
    $arguments = @(
        'search_quota_eight_port_rotations.py',
        '--fixed-routes', $fixedRoutes,
        '--attempts', '120000',
        '--trials', '8',
        '--bend-cost', [string]$bendCosts[$index % $bendCosts.Count],
        '--seed', [string](3026090800 + $index * 1701149),
        '--staging-out', $stagingFile,
        '--json-out', $resultFile
    )
    $processes += Start-Process -FilePath 'python' -ArgumentList $arguments `
        -WorkingDirectory $calibration -RedirectStandardOutput $logFile `
        -RedirectStandardError $errorFile -WindowStyle Hidden -PassThru
}
$processes | Select-Object Id, StartTime | Format-Table -AutoSize
$processes.Id | Set-Content -LiteralPath (Join-Path $outputRoot 'fast8-pids.txt')
