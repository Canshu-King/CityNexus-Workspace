# Weather Runtime Hardening Validation

Date: 2026-09-10

All results below were produced from the real repository after the hardening merge.

## WRH adversarial gate

`python -m pytest -q tests/test_gpt_weather_adversarial_next.py`

Result: **6 passed**. WRH-01 through WRH-06 all pass.

The pre-change baseline was also reproduced: all six tests failed for the expected semantic reasons.

## Combined targeted regression

The required eight-file command covering WRH, WRT, refresh hardening, Provider Runtime, Golden contract, and WP07 foundation completed with **44 passed**.

## Full backend

`python -m pytest -q`

Result: **194 passed, 1 skipped** in 22.18 seconds. The skipped case is the opt-in live-provider smoke test. Two existing Starlette/httpx deprecation warnings remain non-blocking.

Pytest used `D:\moodle\_citynexus_weather_test_tmp` because the system temporary drive had previously been space constrained. This is an environment detail, not a product dependency.

## Static and contract validation

- `python -m compileall -q app tests`: PASS.
- `ruff check app tests`: PASS.
- `ruff format --check app tests`: PASS; 107 files already formatted.
- OpenAPI parity: PASS; formal 39, runtime 39, missing 0, extra 0.

## Frontend and backend-connected Golden

- `npm run build`: PASS.
- `npm run test:e2e`: PASS; 1 passed.
- Scenario: Journey Mode uses backend truth for closure recovery.

The package is validated again after fresh extraction before delivery.
