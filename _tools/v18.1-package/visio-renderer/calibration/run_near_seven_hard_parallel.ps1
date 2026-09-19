$ErrorActionPreference = 'Stop'
$calibration = 'D:\moodle\CityNexus\visio-renderer\calibration'
$outputRoot = Join-Path $calibration 'out\quota_joint_20260908'
$fixedRoutes = Join-Path $outputRoot 'P1_PARTIAL15C_FIXED_ROUTES.yaml'
$overrides = Join-Path $outputRoot 'fast8-4-overrides.yaml'
$near = Join-Path $outputRoot 'fast8-4-repro.near.json'
$triples = @(
    @('A-CE-09','A-M-UC-08','A-CD-UC-04'),
    @('A-CE-09','A-M-UC-08','A-M-UC-04'),
    @('A-CE-09','A-CD-UC-04','A-M-UC-04'),
    @('A-M-UC-08','A-CD-UC-04','A-M-UC-04')
)
$processes = @()
foreach ($index in 0..23) {
    $number = $index + 1
    $triple = $triples[$index % $triples.Count]
    $resultFile = Join-Path $outputRoot ("seven-hard-{0}.json" -f $number)
    $logFile = Join-Path $outputRoot ("seven-hard-{0}.log" -f $number)
    $errorFile = "$logFile.err"
    Remove-Item -LiteralPath $resultFile, $logFile, $errorFile -Force -ErrorAction SilentlyContinue
    $arguments = @('search_near_four_hard.py','--fixed-routes',$fixedRoutes,'--route-overrides',$overrides,'--near',$near)
    foreach ($rid in $triple) { $arguments += @('--release', $rid) }
    $arguments += @('--trials','1500','--seed',[string](8026090800 + $index * 1701149),'--json-out',$resultFile)
    $processes += Start-Process -FilePath 'python' -ArgumentList $arguments `
        -WorkingDirectory $calibration -RedirectStandardOutput $logFile `
        -RedirectStandardError $errorFile -WindowStyle Hidden -PassThru
}
$processes | Select-Object Id, StartTime | Format-Table -AutoSize
$processes.Id | Set-Content -LiteralPath (Join-Path $outputRoot 'seven-hard-pids.txt')
