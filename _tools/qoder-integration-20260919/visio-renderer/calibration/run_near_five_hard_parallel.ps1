$ErrorActionPreference = 'Stop'
$calibration = 'D:\moodle\CityNexus\visio-renderer\calibration'
$outputRoot = Join-Path $calibration 'out\quota_joint_20260908'
$fixedRoutes = Join-Path $outputRoot 'P1_PARTIAL15C_FIXED_ROUTES.yaml'
$overrides = Join-Path $outputRoot 'fast8-4-overrides.yaml'
$near = Join-Path $outputRoot 'fast8-4-repro.near.json'
$releases = @('A-CE-09', 'A-M-UC-08', 'A-CD-UC-04', 'A-M-UC-04')
$processes = @()
foreach ($index in 0..23) {
    $number = $index + 1
    $release = $releases[$index % $releases.Count]
    $resultFile = Join-Path $outputRoot ("five-hard-{0}.json" -f $number)
    $logFile = Join-Path $outputRoot ("five-hard-{0}.log" -f $number)
    $errorFile = "$logFile.err"
    Remove-Item -LiteralPath $resultFile, $logFile, $errorFile -Force -ErrorAction SilentlyContinue
    $arguments = @(
        'search_near_four_hard.py',
        '--fixed-routes', $fixedRoutes,
        '--route-overrides', $overrides,
        '--near', $near,
        '--release', $release,
        '--trials', '4000',
        '--seed', [string](6026090800 + $index * 1701149),
        '--json-out', $resultFile
    )
    $processes += Start-Process -FilePath 'python' -ArgumentList $arguments `
        -WorkingDirectory $calibration -RedirectStandardOutput $logFile `
        -RedirectStandardError $errorFile -WindowStyle Hidden -PassThru
}
$processes | Select-Object Id, StartTime | Format-Table -AutoSize
$processes.Id | Set-Content -LiteralPath (Join-Path $outputRoot 'five-hard-pids.txt')
