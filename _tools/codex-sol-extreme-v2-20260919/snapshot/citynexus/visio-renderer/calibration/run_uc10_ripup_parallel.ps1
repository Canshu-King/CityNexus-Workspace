$ErrorActionPreference = 'Stop'
$calibration = 'D:\moodle\CityNexus\visio-renderer\calibration'
$outputRoot = Join-Path $calibration 'out\quota_joint_20260908'
$fixedRoutes = Join-Path $outputRoot 'uc10-ripup-fixed.yaml'
$routeIds = @('A-B-06','A-CD-UC-10','A-M-UC-10','A-M-UC-08','A-PA-07')
$bendCosts = @(0.05, 0.10, 0.20, 0.35, 0.50, 0.75, 1.00, 1.50)
$processes = @()
foreach ($index in 0..23) {
    $number = $index + 1
    $resultFile = Join-Path $outputRoot ("uc10-ripup-{0}.json" -f $number)
    $stagingFile = Join-Path $outputRoot ("uc10-ripup-{0}.yaml" -f $number)
    $logFile = Join-Path $outputRoot ("uc10-ripup-{0}.log" -f $number)
    $errorFile = "$logFile.err"
    Remove-Item -LiteralPath $resultFile, $stagingFile, $logFile, $errorFile -Force -ErrorAction SilentlyContinue
    $arguments = @('route_p1_negotiated_grid.py','--plan','PLAN_QUOTA_SAVER_NEAR8_PORTS_20260908',
        '--fixed-routes',$fixedRoutes,'--iterations','1000','--seed',[string](8326090800 + $index * 2301239),
        '--bend-cost',[string]$bendCosts[$index % $bendCosts.Count], '--staging-out',$stagingFile,'--json-out',$resultFile)
    foreach ($rid in $routeIds) { $arguments += @('--route-id', $rid) }
    $processes += Start-Process -FilePath 'python' -ArgumentList $arguments `
        -WorkingDirectory $calibration -RedirectStandardOutput $logFile `
        -RedirectStandardError $errorFile -WindowStyle Hidden -PassThru
}
$processes | Select-Object Id, StartTime | Format-Table -AutoSize
$processes.Id | Set-Content -LiteralPath (Join-Path $outputRoot 'uc10-ripup-pids.txt')
