$ErrorActionPreference = 'Stop'
$calibration = 'D:\moodle\CityNexus\visio-renderer\calibration'
$outputRoot = Join-Path $calibration 'out\quota_joint_20260908'
$fixedRoutes = Join-Path $outputRoot 'P1_PARTIAL15C_FIXED_ROUTES.yaml'
$plan = 'PLAN_O_M10_RIGHT_ESCAPE_B06_RIGHT'
$routeIds = @(
    'A-B-06', 'A-PA-07', 'A-CE-09', 'A-CD-UC-10',
    'A-M-UC-08', 'A-M-UC-10', 'A-CD-UC-04', 'A-M-UC-04'
)
$workerCount = 24

$processes = @()
foreach ($index in 0..($workerCount - 1)) {
    $number = $index + 1
    $resultFile = Join-Path $outputRoot ("nego8-{0}.json" -f $number)
    $stagingFile = Join-Path $outputRoot ("nego8-{0}.yaml" -f $number)
    $logFile = Join-Path $outputRoot ("nego8-{0}.log" -f $number)
    $errorFile = "$logFile.err"
    Remove-Item -LiteralPath $resultFile, $stagingFile, $logFile, $errorFile -Force -ErrorAction SilentlyContinue
    $bendCosts = @(0.15, 0.35, 0.60)
    $arguments = @(
        'route_p1_negotiated_grid.py',
        '--plan', $plan,
        '--fixed-routes', $fixedRoutes,
        '--iterations', '1800',
        '--seed', [string](2026090800 + $index * 104729),
        '--bend-cost', [string]$bendCosts[$index % $bendCosts.Count],
        '--staging-out', $stagingFile,
        '--json-out', $resultFile
    )
    foreach ($routeId in $routeIds) {
        $arguments += @('--route-id', $routeId)
    }
    $processes += Start-Process -FilePath 'python' -ArgumentList $arguments `
        -WorkingDirectory $calibration -RedirectStandardOutput $logFile `
        -RedirectStandardError $errorFile -WindowStyle Hidden -PassThru
}
$processes | Select-Object Id, StartTime | Format-Table -AutoSize
$processes.Id | Set-Content -LiteralPath (Join-Path $outputRoot 'nego8-pids.txt')
