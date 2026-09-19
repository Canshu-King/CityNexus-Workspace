# Provider Runtime Hardening Validation

Date: 2026-09-10

## Focused adversarial hardening

Command:

`python -m pytest -q tests/test_gpt_adversarial_provider_hardening.py`

Result: **5 passed**.

## Provider Runtime freeze gate

Command:

`python -m pytest -q tests/test_provider_runtime_gate.py tests/test_gpt_adversarial_provider_hardening.py`

Result: **13 passed**.

This includes the existing PRT-01..PRT-08 gate and PRH-01..PRH-05 hardening tests. PRT-07 covers the offline Golden replan path.

## Full backend

Command:

`python -m pytest -q`

Final result: **170 passed, 1 skipped**.

The skipped test is the opt-in live-provider path. Two Starlette/httpx deprecation warnings are non-blocking.

## Python compile and formatting

- `python -m compileall -q app tests`: PASS.
- `ruff check .`: PASS.
- `ruff format --check .`: PASS, 102 files already formatted.

## OpenAPI parity

Result: **OpenAPI 3.1.0; formal 38; runtime 38; missing 0; extra 0**.

## Frontend

- `npm run build`: PASS.
- `npm run test:e2e`: PASS, **1 passed**.
- Playwright scenario: `Journey Mode uses backend truth for closure recovery`.

## Network/authority checks represented by the gate

- deterministic feasibility consumes frozen evidence;
- JourneyTwin GET does not capture live mobility;
- accept-time revalidation uses persisted frozen mobility evidence;
- offline Golden remains operational;
- no fabricated provider evidence is introduced.
