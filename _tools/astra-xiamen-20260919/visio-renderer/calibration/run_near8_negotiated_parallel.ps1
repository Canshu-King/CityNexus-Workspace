$ErrorActionPreference = 'Stop'
$calibration = 'D:\moodle\CityNexus\visio-renderer\calibration'
$outputRoot = Join-Path $calibration 'out\quota_joint_20260908'
$fixedRoutes = Join-Path $outputRoot 'P1_PARTIAL15C_FIXED_ROUTES.yaml'
$routeIds = @('A-B-06','A-PA-07','A-CE-09','A-CD-UC-10','A-M-UC-08','A-M-UC-10','A-CD-UC-04','A-M-UC-04')
$bendCosts = @(0.10, 0.25, 0.40, 0.60, 0.85, 1.20)
$processes = @()
foreach ($index in 0..23) {
    $number = $index + 1
    $resultFile = Join-Path $outputRoot ("near8-negotiated-{0}.json" -f $number)
    $stagingFile = Join-Path $outputRoot ("near8-negotiated-{0}.yaml" -f $number)
    $logFile = Join-Path $outputRoot ("near8-negotiated-{0}.log" -f $number)
    $errorFile = "$logFile.err"
    Remove-Item -LiteralPath $resultFile, $stagingFile, $logFile, $errorFile -Force -ErrorAction SilentlyContinue
    $arguments = @('route_p1_negotiated_grid.py','--plan','PLAN_QUOTA_SAVER_NEAR8_PORTS_20260908',
        '--fixed-routes',$fixedRoutes,'--iterations','800','--seed',[string](8226090800 + $index * 2101217),
        '--bend-cost',[string]$bendCosts[$index % $bendCosts.Count], '--staging-out',$stagingFile,'--json-out',$resultFile)
    foreach ($rid in $routeIds) { $arguments += @('--route-id', $rid) }
    $processes += Start-Process -FilePath 'python' -ArgumentList $arguments `
        -WorkingDirectory $calibration -RedirectStandardOutput $logFile `
        -RedirectStandardError $errorFile -WindowStyle Hidden -PassThru
}
$processes | Select-Object Id, StartTime | Format-Table -AutoSize
$processes.Id | Set-Content -LiteralPath (Join-Path $outputRoot 'near8-negotiated-pids.txt')
