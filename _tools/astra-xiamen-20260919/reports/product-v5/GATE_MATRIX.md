# CityNexus Live Journey Autopilot V5 — Gate Matrix

Date: 2026-09-12

| Gate | Status | Evidence |
| --- | --- | --- |
| V5-01 model draft cannot increase explicit spending cap | PASS | Supplied `backend/tests/test_gpt_v5_mission_authority.py::test_v5_01_model_cannot_expand_explicit_numeric_authority`; full backend suite. |
| V5-02 model draft cannot erase explicit Activity protection | PASS | Supplied `...::test_v5_02_model_mutable_guess_cannot_erase_explicit_protection`; full backend suite. |
| V5-03 unresolved model references persist | PASS | Supplied `...::test_v5_03_unresolved_model_references_are_persisted`; full backend suite. |
| V5-04 provider fixture changes city conditions without browser-created Events | PASS | Server fixture endpoint and signal pipeline; zero-touch Playwright test uses the fixture endpoint only. |
| V5-05 worker observes ACTIVE Journeys with ACTIVE standing missions | PASS | `backend/app/agent/autorun.py`; `backend/tests/test_v5_autopilot.py`; full regression. |
| V5-06 provider-verified weather evidence can wake Guardian | PASS | Signal ingestion creates provider-owned WEATHER evidence and the Autopilot path reaches Guardian recovery. |
| V5-07 mobility delta produces server-owned TRAFFIC_DELAY evidence | PASS | Mobility snapshot comparison and fixture pipeline in `backend/app/agent/signal_pipeline.py`; V5 provider-event assertions and full regression. |
| V5-08 semantic incident dedup suppresses repeated recovery | PASS | V5 Autopilot test repeats the same fixture and observes no second recovery. |
| V5-09 cooldown is consulted | PASS | Semantic fingerprint/cooldown branch in `backend/app/agent/guardian.py`; Guardian dedup tests and V5 repeat path. |
| V5-10 primary intelligent path uses configured Agent runtime | PASS | Native DeepSeek live smoke completed; Guardian calls `configured_journey_agent()` before fallback. |
| V5-11 deterministic Guardian remains offline fallback | PASS | Zero-touch offline browser/backend E2E records `citynexus-guardian / deterministic-recovery-controller-v1`. |
| V5-12 literal Hermes model-backed run | NOT_RUN_EXTERNAL | No Hermes endpoint/key was configured; no Hermes result is claimed. |
| V5-13 native DeepSeek model-backed run | PASS | Live smoke completed with `deepseek / deepseek-chat` and model-selected MCP V2 tool trace. |
| V5-14 CP-SAT V2 remains primary whole-horizon optimizer | PASS | V5 E2E persisted `ORTOOLS_CP_SAT_V2`; Solver V2 and full backend gates pass. |
| V5-15 autonomous in-envelope recovery mutates Plan without new chat | PASS | V5 zero-touch Playwright test observes executed recovery after provider transition. |
| V5-16 flagship does not click manual Guardian scan | PASS | `frontend/e2e/live-autopilot-v5.spec.ts` asserts zero `/guardian/scan` requests. |
| V5-17 protected Cruise/Dinner/C4 survive | PASS | V5 browser assertions and Gateway/Guardian protection tests. |
| V5-18 over-budget path requires approval | PASS | Guardian and Agent Gateway authority tests in the full backend suite. |
| V5-19 SSE/projection survives reconnect and REST reload | PASS | Backend operations stream plus browser reload assertions for persisted evidence and route state. |
| V5-20 repeated incident creates no second PlanVersion | PASS | V5 backend and browser repeat-dedup assertions. |
| V5-21 provider/model outage preserves deterministic behavior | PASS | Provider degradation and runtime-unavailable fallback tests; deterministic fallback E2E. |
| V5-22 final ZIP excludes caches, dependencies, DBs, and secrets | PASS | Explicit staging allowlist, archive inspection, and fresh-extract replay completed for the final ZIP. |

## Explicit product labels

| Label | Result |
| --- | --- |
| `MISSION_AUTHORITY_MONOTONIC` | `PASS` |
| `CITY_SIGNAL_PIPELINE` | `PASS` |
| `GUARDIAN_AUTORUN` | `PASS` |
| `GUARDIAN_MODEL_ORCHESTRATED` | `PASS` |
| `HERMES_MODEL_BACKED` | `NOT_RUN_EXTERNAL` |
| `NATIVE_DEEPSEEK_MODEL_BACKED` | `PASS` |
| `ORTOOLS_CP_SAT_V2` | `PASS` |
| `ZERO_TOUCH_GUARDIAN_E2E` | `PASS` |
| `LIVE_VALHALLA` | `NOT_RUN_EXTERNAL` |
| `PHOENIX` | `NOT_RUN_OPTIONAL` |
| `PROMPTFOO` | `NOT_RUN_OPTIONAL` |
