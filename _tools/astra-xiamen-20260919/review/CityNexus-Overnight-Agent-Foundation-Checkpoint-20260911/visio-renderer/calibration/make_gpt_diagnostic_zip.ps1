$cal = 'D:\moodle\CityNexus\visio-renderer\calibration'
$out = Join-Path $cal 'out\quota_joint_20260908'
$zip = 'C:\Users\仓鼠王\Downloads\CityNexus-P1-Route-Repair-V3-Codex-Diagnostic-Review-20260908.zip'
if (Test-Path -LiteralPath $zip) { Remove-Item -LiteralPath $zip -Force }
$items = @(
  (Join-Path $cal 'P1_ROUTE_PORT_PLANS.yaml'),
  (Join-Path $cal 'route_p1_negotiated_grid.py'),
  (Join-Path $cal 'search_p1_repaired_pool.py'),
  (Join-Path $cal 'explore_p1_disjoint_pool.py'),
  (Join-Path $cal 'search_quota_cluster_ports.py'),
  (Join-Path $cal 'search_quota_eight_port_rotations.py'),
  (Join-Path $cal 'prepare_uc10_ripup_fixed.py'),
  (Join-Path $cal 'run_near_eight_hard_parallel.ps1'),
  (Join-Path $cal 'run_near8_negotiated_parallel.ps1'),
  (Join-Path $cal 'run_uc10_ripup_parallel.ps1'),
  (Join-Path $out 'GPT-REVIEW-DIAGNOSTIC-20260908.md'),
  (Join-Path $out 'near8-topology.json'),
  (Join-Path $out 'near8-pool.json'),
  (Join-Path $out 'near8-best-witness.json')
)
$items += (Get-ChildItem -LiteralPath $out -File | Where-Object { $_.Name -like 'seven-hard-*.json' }).FullName
$items += (Get-ChildItem -LiteralPath $out -File | Where-Object { $_.Name -like 'eight-hard-*.json' }).FullName
$items += (Get-ChildItem -LiteralPath $out -File | Where-Object { $_.Name -like 'near8-negotiated-*.json' }).FullName
Compress-Archive -LiteralPath $items -DestinationPath $zip -CompressionLevel Optimal
Get-Item -LiteralPath $zip | Select-Object FullName,Length,LastWriteTime
