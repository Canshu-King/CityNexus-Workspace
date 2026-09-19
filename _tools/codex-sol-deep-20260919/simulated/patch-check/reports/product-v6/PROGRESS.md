# CityNexus Predictive Real-City Twin V6 — Progress

Date: 2026-09-12  
Repository: `D:\moodle\CityNexus`

## Current status

The V6 implementation is complete against the supplied goal. The V5 milestone remains green, and the new completion gate is green: the browser drives a forecast risk through the server-owned provider pipeline, CityNexus computes a resilience weakness and bounded counterfactuals, discovers a replay-backed real-city alternative, runs CP-SAT V2, applies the Delegation Policy, changes the active Plan before hard infeasibility, and preserves the protected Cruise/C4 commitment.

## Work completed

- Read and applied `CODEX_START_HERE.txt`, `CODEX_NEXT_GOAL.txt`, `README.md`, `REVIEW_FINDINGS.md`, and all V6 contracts from the supplied assist package. The assist package was kept outside the final source archive.
- Preserved the V5 signal pipeline, Mission Authority V2, Guardian pulse/dedup/cooldown, deterministic fallback, CP-SAT V2, Agent Gateway, SSE/projection, JourneyTwin, C4 protection, and Golden paths.
- Added persisted per-Journey `AutopilotEnrollment` records. The worker remains process-global, but it scans only enabled Journey subscriptions. Starting or stopping one Journey no longer silently changes another Journey.
- Added composite provider evidence with independent provider state, provenance, capture time, and TTL. Deterministic projections consume captured observations and do not make live network calls.
- Added Open-Meteo, Valhalla HTTP, Nominatim, Overpass, and OpenFreeMap integration seams with identified requests and bounded calls. A live discovery failure returns explicit `replay-fallback`/`REPLAY` evidence instead of being reported as live success.
- Added provider-backed real-city candidate materialization into `RealPlaceCandidate`, `Place`, and `CityService`. The replay path is Tianjin-oriented and stable for deterministic demonstrations.
- Added `JourneyResilienceSnapshot` with commitment slack, weather exposure, mobility sensitivity, recovery optionality, cost headroom, route/geography exposure, single-point-of-failure, activity risk, dominant failure modes, recommendation, and provider provenance.
- Added six bounded counterfactual scenarios: earlier rain, route delay +10/+20/+30 minutes, mutable place closure, and replacement disappearance. Simulations reuse JourneyTwin/CP-SAT V2 and never mutate Domain Truth.
- Added predictive Guardian execution. A forecast trigger can autonomously replan before hard failure when the risk reduction, reversibility, provider state, protected commitments, loss limits, and user envelope permit it. The deterministic layer verifies the resulting Journey facts; it does not replace model semantic interpretation.
- Added predictive event/run markers and stable snapshot fingerprints so high-frequency pulses deduplicate after successful prevention and do not create repeated plans.
- Added the Control Tower resilience/real-city/provider mesh panels and OpenFreeMap-backed MapLibre metadata while retaining route and place fallback evidence.
- Added V6 backend and browser flagship coverage, including per-Journey enrollment, replay fallback, predictive prevention, counterfactual immutability, real POI materialization, reload persistence, and V5 regression behavior.

## Final validation

| Check | Result |
| --- | --- |
| V6 + V5 + V4 focused backend gates | **8 passed, 2 warnings** |
| Full backend pytest | **323 passed, 2 skipped, 2 warnings** |
| Ruff check | **passed** |
| Ruff format check | **passed** |
| Python compileall | **passed** |
| Frontend production build | **passed** |
| Full Playwright suite | **7 passed** |
| V6 Predictive Real-City Twin browser gate | **passed** |
| Live provider smoke | Open-Meteo, Nominatim, Overpass, Valhalla, and OpenFreeMap passed |
| Native DeepSeek Agent smoke | **passed**; `deepseek / deepseek-chat`, completed tool loop |
| Hermes model-backed smoke | **NOT_RUN_EXTERNAL**; no Hermes endpoint/key configured |
| Phoenix trace | **NOT_RUN_OPTIONAL** |
| Promptfoo evaluation | **NOT_RUN_OPTIONAL** |

The two pytest warnings are the existing Starlette/httpx deprecation warnings. No test failure is being hidden by the warnings.

## Security and packaging

The temporary DeepSeek credential was read only into a child process for smoke tests. It was not printed, committed, written to source, reports, audit payloads, database rows, browser artifacts, or the final ZIP. The final archive excludes credentials, databases, caches, dependencies, build output, browser reports, and nested archives.
