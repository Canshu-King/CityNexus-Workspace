# Gate matrix

| Gate | Evidence | Result |
| --- | --- | --- |
| Prepared patch preflight | `git apply --check --verbose` on the supplied patch (8 targets) | PASS |
| WP06 follow-up | `backend/tests/test_wp06_followup_assist.py` and prior regression tests | PASS |
| F3 | Integrated opportunity-window candidate test and authoritative feasibility | PASS |
| Valhalla/MobilitySnapshot | Offline HTTP adapter/snapshot tests; live smoke explicitly skipped | PASS / OPTIONAL LIVE SKIP |
| Open-Meteo | Server-side provider-verified ingestion regression | PASS |
| OR-Tools | Optional adapter boundary test; no mandatory import | PASS |
| LiteLLM/DeepSeek | Verified-facts contract and deterministic resilient fallback tests | PASS |
| Frontend | `npm run build` | PASS |
| Playwright | `npm run test:e2e` (`e2e/golden.spec.ts`) | PASS |
| API contract | OpenAPI 3.1 parse and exact 38/38 operation comparison | PASS |
| Full backend | `python -m pytest -q` from `backend/` | 144 passed, 1 skipped |

