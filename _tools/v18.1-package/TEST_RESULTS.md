# CityNexus V18 Test Results

Captured from `D:\moodle\CityNexus` during the V18 convergence window. The
release filename remains the requested `20260914` target; the final checks
crossed midnight Asia/Shanghai on 2026-09-15.

| Gate | Result |
| --- | --- |
| V18 semantic time, verification, Hermes client | **4 passed, 2 warnings** |
| V17 semantic compiler + OpenAPI contract + MCP V2 boundary | **18 passed, 2 warnings** |
| V16 integration + V15 Copilot + V14 recovery/trial readiness | **20 passed, 2 warnings** |
| Broad backend regression | **421 passed, 2 skipped, 2 warnings** |
| Frontend production build | **PASS; Vite 7.3.6, 1,904 modules** |
| Desktop Playwright flow | **PASS; fresh sealed Journey + Copilot EXPLAIN_PLAN** |
| Mobile Playwright flow | **PASS; Copilot WHAT_IF remained read-only** |
| Native Hermes model mission | **NOT CONFIGURED; no provider credential or loopback server key** |
| Fresh-extract runtime gate | **PASS; 22 focused tests from the fresh extraction** |

The two warnings are existing FastAPI/Starlette/httpx deprecations.
## 2026-09-15 V18.1

- Native contract tests: 3 passed.
- Frontend production build: passed (`vite build`).
- Copilot proof: completed native run `run_101e85d4093e49bdbb1ae5ea35c3a4ef`.
- Observed actual MCP events: `mcp__citynexus__list_replans` started/completed.
- Hermes correctly refused a replan proposal because the demo Journey had no
  authoritative trigger event; no mutation was performed.
