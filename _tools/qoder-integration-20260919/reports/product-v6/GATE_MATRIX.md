# CityNexus Predictive Real-City Twin V6 — Gate Matrix

Date: 2026-09-12

| Gate | Status | Evidence |
| --- | --- | --- |
| V6-01 Worker lifecycle is global but enrollment is per Journey | PASS | `backend/app/agent/autorun.py`; `backend/tests/test_v6_enrollment.py`; full backend suite. |
| V6-02 Starting Journey A does not enroll Journey B | PASS | Per-Journey enrollment test creates A, enables only A, and asserts the enrolled set contains only A. |
| V6-03 Stopping Journey A does not disable Journey B | PASS | Per-Journey enrollment test enables A and B, disables A, and asserts B remains enabled. |
| V6-04 Live signal refresh composes weather and mobility | PASS | `SignalPipelineResult.provider_states/provider_provenance`; composite pulse provider; V6 replay mesh evidence. |
| V6-05 Observations carry state, provenance, capture time, and TTL | PASS | `ProviderObservation` schema/model and provider observation persistence; full backend suite. |
| V6-06 Real Nominatim geocoding smoke | PASS | Identified one-call smoke returned `nominatim:relation/912999` for Tianjin. |
| V6-07 Real Overpass bounded POI smoke | PASS | Identified bounded query returned two candidates around Tianjin. |
| V6-08 Real POIs materialize with stable provider/external IDs | PASS | `RealPlaceCandidate` materialization into `Place`/`CityService`; V6 E2E selects `real-place-*` and persists provider evidence. |
| V6-09 Real Valhalla route smoke and honest fallback | PASS | Public fair-use `valhalla1.openstreetmap.de` smoke returned an 18-minute route; adapter and fallback tests remain green. |
| V6-10 MapLibre real basemap and route evidence | PASS | OpenFreeMap Liberty style returned HTTP 200; browser asserts `data-basemap-provider="openfreemap"` and persisted route evidence. |
| V6-11 Literal Hermes model-backed loop | NOT_RUN_EXTERNAL | Hermes adapter exists, but no Hermes endpoint/key was configured; no Hermes result is claimed. |
| V6-12 Native DeepSeek model-backed loop | PASS | Process-only live smoke completed `deepseek / deepseek-chat` with `inspect_journey → inspect_twin → list_replans → request_replan → list_replans → accept_replan`. |
| V6-13 Resilience snapshot deterministic for frozen facts | PASS | Stable provider fingerprint plus repeated V6 pulse returns the same predictive Guardian run with `deduplicated=true`. |
| V6-14 Snapshot includes required resilience components | PASS | V6 assertion checks forecast risk and browser renders score/status/failure modes; implementation persists all required components. |
| V6-15 Counterfactuals do not mutate Domain Truth | PASS | Six simulations returned `JourneyTwin + CP-SAT V2` evidence and `domain_truth_mutated=false`. |
| V6-16 Preemptive recovery before hard failure | PASS | V6 browser path starts from `RISK_FORECAST`, reaches `PREDICTIVE_WEAKNESS`, and changes the Plan before a hard disruption. |
| V6-17 Preemptive action obeys envelope and protected commitments | PASS | Browser observes `ALLOW_AUTO`, `EXECUTED`, preserved Cruise, and the protected C4 assertions; policy tests cover gated paths. |
| V6-18 Real-city replacement feeds CP-SAT V2 | PASS | V6 backend/browser evidence records `ORTOOLS_CP_SAT_V2` and selects a materialized real-place replacement. |
| V6-19 Control Tower shows POIs, basemap, route provenance, and resilience | PASS | V6 browser assertions cover resilience panel, real POI text, map provider marker, route evidence, and reload persistence. |
| V6-20 Phoenix trace | NOT_RUN_OPTIONAL | Phoenix/OpenInference is not configured in this workspace. |
| V6-21 Promptfoo adversarial evaluation | NOT_RUN_OPTIONAL | Promptfoo is not configured in this workspace. |
| V6-22 Live-mode failure falls back to replay | PASS | Live discovery now returns explicit `mode=replay-fallback`, `provenance=REPLAY`, provider fallback statuses, and a reason; V6 backend test covers disabled-live fallback. |
| V6-23 Offline deterministic Golden remains green | PASS | Full Playwright suite includes Golden and V5 paths; full backend suite passes. |
| V6-24 Final ZIP hygiene | PASS | Final staging allowlist and archive scan exclude keys, databases, caches, dependencies, build output, browser reports, and nested ZIPs. |

## Required product labels

| Label | Result |
| --- | --- |
| `V5_REGRESSION` | `PASS` |
| `PER_JOURNEY_AUTOPILOT` | `PASS` |
| `COMPOSITE_PROVIDER_MESH` | `PASS` |
| `LIVE_OPEN_METEO` | `PASS` |
| `LIVE_VALHALLA` | `PASS` |
| `LIVE_NOMINATIM` | `PASS` |
| `LIVE_OVERPASS` | `PASS` |
| `REAL_POI_DISCOVERY` | `PASS` |
| `OPENFREEMAP_BASEMAP` | `PASS` |
| `HERMES_MODEL_BACKED` | `NOT_RUN_EXTERNAL` |
| `NATIVE_DEEPSEEK_MODEL_BACKED` | `PASS` |
| `PREDICTIVE_RESILIENCE` | `PASS` |
| `COUNTERFACTUAL_TWIN` | `PASS` |
| `PREEMPTIVE_AUTOPILOT` | `PASS` |
| `REAL_CITY_E2E` | `PASS` |
| `PHOENIX_TRACE` | `NOT_RUN_OPTIONAL` |
| `PROMPTFOO_EVAL` | `NOT_RUN_OPTIONAL` |
