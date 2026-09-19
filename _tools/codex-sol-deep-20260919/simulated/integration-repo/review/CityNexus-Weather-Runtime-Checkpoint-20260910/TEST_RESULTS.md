# Weather Runtime Validation

Date: 2026-09-10

## Weather acceptance gate

`python -m pytest -q tests/test_weather_runtime_gate_gpt.py`

Result: **12 passed**. This covers WRT-01 through WRT-12.

## Weather hardening and trigger boundary

`python -m pytest -q tests/test_weather_runtime_hardening.py tests/test_weather_refresh_endpoint.py`

Result: **5 passed**.

The additional checks cover UTC normalization, exact coordinate scope matching, coordinate-aware Event identity, server-owned provider invocation, and rejection of client-supplied weather facts.

## Existing regression gate

`python -m pytest -q tests/test_provider_runtime_gate.py tests/test_gpt_adversarial_provider_hardening.py tests/test_backend_connected_golden_contract.py tests/test_wp07_foundation_assist.py`

Result: **21 passed**.

## Full backend

`python -m pytest -q`

Final result: **188 passed, 1 skipped**. The skipped test is the opt-in live-provider smoke path. Two existing Starlette/httpx deprecation warnings remain non-blocking.

The test run used `D:\moodle\_citynexus_weather_test_tmp` for pytest temporary files because the system C drive had no free space; this is an environment constraint, not a product dependency.

## Static and contract validation

- `python -m compileall -q app tests`: PASS.
- `ruff check app tests`: PASS.
- `ruff format --check app tests`: PASS, 106 files already formatted.
- OpenAPI parity: **formal 39 / runtime 39 / missing 0 / extra 0**.
- Contract test: 3 passed, including bodyless server-owned weather refresh.

## Frontend

- `npm run build`: PASS.
- `npm run test:e2e`: PASS, **1 passed**.
- Golden scenario: Journey Mode uses backend truth for closure recovery.
