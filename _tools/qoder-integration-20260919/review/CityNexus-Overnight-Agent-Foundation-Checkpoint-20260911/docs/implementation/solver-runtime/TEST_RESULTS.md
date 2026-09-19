# Solver Runtime V1 Validation

Date: 2026-09-10

## Test-first baseline

The three supplied solver test files initially failed collection because the four solver modules did not exist. After adding the dependency-free reference layer, the baseline produced 15 passed and 2 skipped before OR-Tools installation.

OR-Tools `9.15.6755` was then installed in the Windows project virtual environment. The real CP-SAT tests ran and the supplied/reference set produced **16 passed, 1 conditional skip**.

## ORT-01 through ORT-20

`python -m pytest -q tests/test_solver_runtime_gate.py`

Result: **20 passed**. This includes real Replan/DB tests for immutable completed prefix and C4, one frozen snapshot, malicious solver assignment rejection, opening and budget rechecks, controlled fallback, offline acceptance, provenance, stable/unique Top-K, accept-time revalidation, candidate count, orphan cleanup, and disabled mode.

## Focused inherited regression

Solver/reference tests plus Provider, Weather, and backend-connected Golden checks: **73 passed, 1 skipped**.

## Full backend

`python -m pytest -q`

Result: **230 passed, 2 skipped, exit code 0** in 28.22 seconds. The skips are the opt-in live-provider smoke test and the inverse optional-dependency test that only runs when OR-Tools is absent. Two existing Starlette/httpx deprecation warnings remain non-blocking.

## Static, contracts, and frontend

- `python -m compileall -q app tests`: PASS.
- `ruff check app tests`: PASS.
- `ruff format --check app tests`: PASS; 115 files formatted.
- Solver static boundary: PASS; 4 modules checked.
- OpenAPI parity: PASS; formal 39, runtime 39, missing 0, extra 0.
- `npm run build`: PASS.
- Backend-connected Playwright Golden: PASS; 1 passed.

The final review ZIP is independently extracted and validated again before delivery.
