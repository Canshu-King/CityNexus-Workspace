$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $PSScriptRoot
$Backend = Join-Path $Root "backend"

Push-Location $Backend
try {
    python -m pytest -q `
        tests/test_solver_reference_contract.py `
        tests/test_ortools_optional_boundary.py `
        tests/test_solver_runtime_policy.py `
        tests/test_solver_runtime_gate.py
    python -m pytest -q `
        tests/test_gpt_weather_adversarial_next.py `
        tests/test_weather_runtime_gate_gpt.py `
        tests/test_weather_runtime_hardening.py `
        tests/test_weather_refresh_endpoint.py `
        tests/test_provider_runtime_gate.py `
        tests/test_gpt_adversarial_provider_hardening.py `
        tests/test_backend_connected_golden_contract.py
    python -m pytest -q
    python -m compileall -q app tests
    ruff check app tests
    ruff format --check app tests
    python (Join-Path $PSScriptRoot "check_solver_static_boundary.py") .
} finally {
    Pop-Location
}

Push-Location $Root
try {
    python (Join-Path $PSScriptRoot "verify_openapi_parity.py")
} finally {
    Pop-Location
}
