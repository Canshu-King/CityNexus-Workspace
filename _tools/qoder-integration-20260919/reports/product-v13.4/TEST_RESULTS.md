# V13.4 Test Results

## Focused convergence

```text
backend/tests/test_v13_4_provider_truth.py
backend/tests/test_v13_3_real_city_intelligence.py
backend/tests/test_v7_traveler_twin.py
7 passed, 2 warnings
```

The focused tests cover official evidence promotion, rejection of unsourced model facts, safe DeepSeek diagnostics, the V13.3 real-city Golden, and the preserved V7 TravelerTwin loop.

## Broad backend regression

```text
python -m pytest -q backend/tests
388 passed, 2 skipped, 2 warnings in 50.92s
```

The first convergence run exposed one stale V7 expectation for the old direct-discovery label `SEALED_LIVE_CAPTURE`. The final implementation preserves that legacy direct-response alias while the V13.4 orchestration contract consumes `runtime_provenance=SEALED_REAL_REPLAY`; the rerun was green.

## Frontend and browser

- `npm run build`: passed before final backend-only compatibility adjustment; Vite emitted only the existing large-chunk advisory.
- Playwright `/v8/discover`: passed to selected PlanVersion with sealed-real provenance, official source evidence, rejected unknown candidates, and visible deterministic gate status.

## Fresh-extract gate

The first release candidate was extracted outside the repository and executed successfully:

```text
backend/tests/test_v13_4_provider_truth.py
backend/tests/test_v13_3_real_city_intelligence.py
5 passed, 2 warnings in 4.40s

npm ci --ignore-scripts --no-audit --no-fund
added 708 packages
npm run build
Vite production build: PASS
```

The source worktree virtual environment was used only as an external test runtime; the imported modules, tests, data, and frontend source all came from the fresh extraction. The archive itself contains no virtual environment, database, cache, frontend build output, or browser state.
