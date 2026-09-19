$ErrorActionPreference = "Stop"

$Repo = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$Backend = Join-Path $Repo "backend"
$Python = Join-Path $Repo ".venv\Scripts\python.exe"
if (-not (Test-Path -LiteralPath $Python)) {
    $Python = "python"
}

Push-Location $Backend
try {
    & $Python -m pytest -q tests/test_gpt_solver_hardening_next.py
    & $Python -m pytest -q tests/test_solver_runtime_gate.py
    & $Python -m pytest -q tests/test_agent_runtime_gate.py
    & $Python -m pytest -q
    & $Python -m compileall -q app tests
    & $Python -m ruff check app tests
    & $Python -m ruff format --check app tests
}
finally {
    Pop-Location
}

Push-Location $Repo
try {
    & $Python tools/verify_openapi_parity.py
    & $Python tools/check_solver_static_boundary.py backend
    & $Python -m pytest -q agent-mcp/tests
}
finally {
    Pop-Location
}

if (Test-Path -LiteralPath (Join-Path $Repo "frontend\package.json")) {
    Push-Location (Join-Path $Repo "frontend")
    try {
        npm run build
        $env:CITYNEXUS_PYTHON = $Python
        npm run test:e2e
    }
    finally {
        Pop-Location
    }
}

