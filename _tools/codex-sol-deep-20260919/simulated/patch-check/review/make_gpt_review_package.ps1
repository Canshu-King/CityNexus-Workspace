$out = 'D:\moodle\CityNexus\review\GPT-Deep-Assist-Review-20260908'
$zip = 'C:\Users\仓鼠王\Downloads\CityNexus-P1-Codex-Deep-Assist-Review-20260908.zip'
if (Test-Path -LiteralPath $out) { Remove-Item -LiteralPath $out -Recurse -Force }
New-Item -ItemType Directory -Force -Path $out,(Join-Path $out 'assist'),(Join-Path $out 'diagnostics'),(Join-Path $out 'tests'),(Join-Path $out 'patches') | Out-Null
$incoming = 'D:\moodle\CityNexus\review\_incoming_deep_assist_20260908\CityNexus-P1-Codex-Deep-Assist-20260908'
Copy-Item -LiteralPath "$incoming\README.md","$incoming\CODEX_NEXT_INSTRUCTION.md","$incoming\FINDINGS.md","$incoming\ASSIST-SUMMARY.json" -Destination "$out\assist"
$cal = 'D:\moodle\CityNexus\visio-renderer\calibration'
Copy-Item -LiteralPath "$cal\search_p1_local_bundle_ports.py","$cal\search_p1_repaired_pool.py","$cal\route_candidate_selector.py","$cal\explore_p1_disjoint_pool.py","$cal\route_p1_negotiated_grid.py" -Destination "$out\patches"
$diag = 'D:\moodle\CityNexus\visio-renderer\calibration\out'
Copy-Item -LiteralPath "$diag\localbundle-par-*.json","$diag\localbundle-source-*.json","$diag\localbundle-left-*.json","$diag\repaired-par-*.log","$diag\trav-planar-01.yaml","$diag\P1-TOPOLOGY-TRAVELER-PLANAR-GRID.json" -Destination "$out\diagnostics"
Push-Location 'D:\moodle\CityNexus\visio-renderer'
python -m pytest -q tests *> "$out\tests\pytest-tests.txt"
$pytestExit = $LASTEXITCODE
python -m compileall -q calibration *> "$out\tests\compileall.txt"
$compileExit = $LASTEXITCODE
Pop-Location
$summary = @"
# CityNexus P1 Deep Assist Review Package

Date: 2026-09-08
Scope: P1_UC_Overview Association route-planning repair.

## Result

No official candidate or frozen Extend route was modified. This run did not produce an 18/18 staging candidate.

## Parallel search

- 8 local bundle workers with target-side variants: all genus=0; AC-3 emptied A-T-UC-06 or A-T-UC-07.
- 8 source-port workers: all genus=0; AC-3 emptied A-T-UC-07.
- 8 left-inclusive plus source-port workers: all genus=0; AC-3 emptied A-T-UC-07; one run emptied A-B-06.
- 4 full repaired-pool workers: AC-3 proved the current full pools infeasible; dominant empty domain was A-T-UC-07.

## Verification

- pytest exit code: $pytestExit
- compileall exit code: $compileExit
- See tests/pytest-tests.txt and tests/compileall.txt for command output.

## GPT review request

Review the attached diagnostics and advise on a broader topology-preserving port/corridor strategy for the UC-06/UC-07 five-route bundle. Treat all local PASS/FAIL data as experimental evidence only. Do not promote RC6, render Visio, or alter frozen Extend geometry.
"@
Set-Content -LiteralPath "$out\REVIEW-SUMMARY.md" -Value $summary -Encoding UTF8
if (Test-Path -LiteralPath $zip) { Remove-Item -LiteralPath $zip -Force }
Compress-Archive -Path "$out\*" -DestinationPath $zip -CompressionLevel Optimal
Get-Item -LiteralPath $zip | Select-Object FullName,Length,LastWriteTime
