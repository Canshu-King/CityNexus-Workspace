# Provider Runtime Validation Evidence

Date: 2026-09-10

## Tests-first baseline

Initial PRT-01..PRT-08 run before runtime wiring:

```text
6 failed, 2 passed
```

Observed failures proved that Replan did not call an operation capture boundary,
provider evidence remained `mock-mobility`, snapshot evidence lacked operation
metadata/serialization, and Twin exposed no persisted mobility snapshot context.

## Provider Runtime gate

```text
tests/test_provider_runtime_gate.py
8 passed
```

PRT-01 Same Operation / Same Snapshot: PASS

PRT-02 Valhalla provenance: PASS

PRT-03 Partial pair-level fallback: PASS

PRT-04 No fabricated ETA: PASS

PRT-05 No network/live provider call inside deterministic gate: PASS

PRT-06 JourneyTwin read-safe frozen evidence: PASS

PRT-07 Offline Golden regression: PASS

PRT-08 `httpx.MockTransport` Valhalla -> snapshot -> gate: PASS

## Focused compatibility gate

Provider Runtime + previous provider foundation + snapshot + backend Golden +
Post-Goal five-defect + Vertical Slice hardening tests:

```text
25 passed
```

## Full backend

```text
165 passed, 1 skipped, 2 warnings
```

Skipped: opt-in live Valhalla smoke when no endpoint is configured.

Warnings: upstream Starlette/httpx TestClient and AnyIO deprecations.

## Static / contract checks

```text
compileall: PASS
ruff check: PASS
ruff format --check: PASS
OpenAPI 3.1.0; formal 38; runtime 38
missing 0; extra 0
```

## Frontend / end-to-end regression

```text
npm run build: PASS
npm run test:e2e: 1 passed
```

The Playwright scenario remains backend-connected and exercises Journey Mode
closure recovery rather than localStorage domain truth.

## Fresh-extract replay

The self-contained review ZIP was extracted into a new directory and replayed:

```text
backend full suite: 165 passed, 1 skipped
OpenAPI parity: formal 38, runtime 38, missing 0, extra 0
npm ci: PASS
npm run build: PASS
npm run test:e2e: PASS
```

The Playwright backend launcher supports `CITYNEXUS_PYTHON` so an external
reviewer can point the extracted package at an existing Python environment
without requiring a `.venv` inside the archive.
