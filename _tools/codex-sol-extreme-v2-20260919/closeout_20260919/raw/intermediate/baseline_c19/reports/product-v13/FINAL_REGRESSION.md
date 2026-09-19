# V13 Final Regression Record

The commands below were run against the current worktree. Historical extracted
archives under the repository were not treated as product source. A mistaken
root-level pytest discovery was stopped after it entered those archives; the
supported backend-scoped command is the authoritative result.

| Surface | Command/result | Status |
| --- | --- | --- |
| Backend full suite | From `backend`: `..\.venv\Scripts\python.exe -m pytest -q --disable-warnings` → `369 passed, 2 skipped, 2 warnings` (38.54s, latest run) | **PASS** |
| V13 integrity | `backend/tests/test_v13_integrity.py` → `22 passed, 2 warnings` (11.11s, latest run) | **PASS** |
| V12/V13 focused | Authoritative V12 + V13 contract suites green; V5 and V7 targeted regressions green | **PASS** |
| V5/V6 repeated browser | `live-autopilot-v5.spec.ts predictive-real-city-v6.spec.ts --repeat-each=3` → `6 passed` (38.5s) | **PASS** |
| Product-hardening browser | `product-hardening.spec.ts --repeat-each=3` → `15 passed` (25.1s), including repeated reload after assisted/autonomous recovery | **PASS** |
| V9 offline browser | `real-world-trip-operations-v9.spec.ts` → `1 passed` (7.7s) after single-worker offline cache repair | **PASS** |
| Full Playwright | `npm run test:e2e -- --reporter=line` from `frontend` → `16 passed` (33.9s), after single-worker/offline-cache and async-state hydration fixes | **PASS** |
| Full Playwright stress | `npm run test:e2e -- --repeat-each=2 --reporter=line` → `32 passed` (1.1m), including the second-cycle Guardian reset boundary | **PASS** |
| Production frontend | `npm run build` → Vite 7.3.6 build complete, 1,897 modules, `dist/v10-sw.js` generated after the single-worker patch | **PASS**, large-chunk warning |
| Storybook | `npm run storybook:build` complete, 1,974 modules after the single-worker patch | **PASS**, large-chunk warnings |
| OpenAPI parity | `verify_openapi_parity.py` → OpenAPI 3.1.0; formal 119/runtime 119; missing 0/extra 0 | **PASS** |
| Solver boundary | `check_solver_static_boundary.py backend` → `SOLVER STATIC BOUNDARY PASS (4 modules checked)` | **PASS** |
| MCP | `agent-mcp`: `6 passed` | **PASS** |
| Local adversarial adapter | `evals/promptfoo/run_local.py` → `13/13`; label `PASS_LOCAL_DETERMINISTIC_ADAPTER` | **PASS LOCAL**, not literal Promptfoo/model-backed |
| Python syntax | `compileall` over backend/agent-mcp | **PASS** |
| Secret scan | current tracked source scope → credential values absent | **PASS** |
| Real-city replay | Tianjin sealed snapshot contains captured Nominatim/Valhalla/Open-Meteo facts; Overpass is explicitly `NO_RESULTS` | **PASS REPLAY**, not live capture |

The two skips are existing environment-dependent tests. Build warnings are
bundle-size warnings, not functional failures. DeepSeek/Hermes/Phoenix are not
configured in the current process and are reported as external boundaries.

## Final convergence rerun

The following rerun is the authoritative post-gate result, captured at
`2026-09-13T11:59:20.8892854+08:00` Asia/Shanghai, after the required
`2026-09-13T11:38:15.3131334+08:00` earliest-final timestamp:

| Surface | Final result | Status |
| --- | --- | --- |
| Backend full suite | `369 passed, 2 skipped, 2 warnings` in `55.71s` | **PASS** |
| V13/V5/V6 focused suite | `25 passed, 2 warnings` in `23.25s` | **PASS** |
| Full Playwright | `16 passed` in `42.2s` | **PASS** |
| Production frontend | Vite 7.3.6, 1,897 modules, `dist/v10-sw.js`; built in `7.88s` | **PASS**, large-chunk warning |
| Storybook | 1,974 modules; built in `7.16s` | **PASS**, large-chunk warnings |
| OpenAPI parity | formal 119 / runtime 119; missing 0 / extra 0 | **PASS** |
| Solver boundary | 4 modules checked | **PASS** |
| Agent MCP | `6 passed` in `2.30s` | **PASS** |
| Local adversarial adapter | `13/13`; deterministic local adapter label | **PASS LOCAL**, not literal Promptfoo/model-backed |
| Python compile and diff check | `PY_COMPILE_PASS`; `git diff --check` clean | **PASS** |
| Secret scan | no literal credential matches in package source/report scope | **PASS** |
| Sealed Tianjin replay | 5 candidates, 36 mobility facts, 24 weather hours; captured providers explicit | **PASS REPLAY**, not live capture |

The previously recorded full-browser stress result remains valid: the matrix
passed `32/32` with `--repeat-each=2`, including the second-cycle worker reset
boundary. The final single-run matrix above was rerun after the wall-clock gate.
