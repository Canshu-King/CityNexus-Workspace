$ErrorActionPreference = "Stop"

Set-Location "D:\moodle\CityNexus\backend"
$env:PYTHONPATH = "."

Write-Host "[1/5] Weather Runtime WRT-01..WRT-12"
pytest -q tests/test_weather_runtime_gate_gpt.py
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "[2/5] Provider + Golden regressions"
pytest -q tests/test_provider_runtime_gate.py tests/test_gpt_adversarial_provider_hardening.py tests/test_backend_connected_golden_contract.py tests/test_wp07_foundation_assist.py
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "[3/5] Full backend"
pytest -q
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "[4/5] Compile"
python -m compileall -q app tests
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "[5/5] Ruff"
ruff check app tests
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "Weather Runtime backend gate PASS"
