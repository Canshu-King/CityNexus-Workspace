# CityNexus V7 Gate Matrix

Runtime labels are deliberately explicit. `PASS` means the local gate was executed and passed; `PARTIAL` means the product fallback is verified but an optional external runtime was not completed.

| Required label | Result | Evidence |
| --- | --- | --- |
| `V6_REGRESSION` | PASS | Full backend pytest: 326 passed, 2 skipped; V4/V5/V6 focused tests included; Playwright V5/V6 flows passed. |
| `REAL_CITY_TRUTH_V2` | PASS_WITH_EXPLICIT_UNKNOWN | Journey-derived anchor; Nominatim grounding; Overpass category attempt; normalized `UNKNOWN` opening/cost evidence never promoted to all-day/zero-cost truth. |
| `LIVE_CAPTURE_REPLAY` | PASS | Fresh `data/replay/tianjin_real_snapshot.json`; captured-replay endpoint returned `SEALED_LIVE_CAPTURE`; replay was exercised by the V7 test. |
| `OUTCOME_TELEMETRY` | PASS | Append-only actual start/complete/skip/manual/agent/user outcome API and Reflect timeline; no planned timestamp substituted for actual time. |
| `TRAVELER_TWIN` | PASS | Persisted explicit and `LEARNED_SOFT` evidence, confidence, count, recency, conflicts, explanation, inspect endpoint, and learned-clear endpoint; indoor and low-walking cross-Journey dimensions are covered. |
| `REFLECT_LEARN_LOOP` | PASS | Journey completion and `/reflect/process` update the materialized TravelerTwin projection with bounded evidence. |
| `PERSONALIZED_CP_SAT` | PASS | Learned fit participates in candidate ranking and V2 soft objective; deterministic feasibility remains authoritative. |
| `RESILIENCE_V2` | PASS | Provider-derived bounded scenarios, heuristic uncertainty labels, risk/switching/preventive value, true protected-anchor slack, and hard gate. |
| `HERMES_MODEL_BACKED` | PARTIAL_NOT_RUN_EXTERNAL | Official Windows install was attempted in `D:\moodle\_hermes_v7_runtime`; prerequisite stages passed but GitHub clone failed. No Hermes CLI E2E claim. |
| `NATIVE_DEEPSEEK_MODEL_BACKED` | PASS | Real DeepSeek tool loop completed with provider `deepseek`; tools included inspect, replan, and city search; trace ID persisted. |
| `PHOENIX_TRACE` | PASS_LOCAL_OPTIONAL_EXPORTER | Local OpenInference-shaped spans are persisted and inspectable; `CITYNEXUS_PHOENIX_ENDPOINT` was not configured, so no external Phoenix claim is made. |
| `PROMPTFOO_EVAL` | PASS_LOCAL_DETERMINISTIC_ADAPTER | 13/13 adversarial cases passed without a secret in config/output. npm Promptfoo CLI was attempted but blocked by C: drive `ENOSPC`. |
| `CROSS_JOURNEY_PERSONALIZATION_E2E` | PASS | Journey A actual outcomes → learned indoor signal → Journey B ranking and predictive autonomous recovery → Journey C explicit outdoor override. |
| `EXPLICIT_PREFERENCE_OVERRIDE` | PASS | Mission-local explicit outdoor preference suppresses learned indoor evidence for that Journey. |
| `NO_AUTHORITY_ESCALATION` | PASS | TravelerTwin is soft planning input only; policy/envelope, commitment, booking, budget, and provider gates remain server-owned. |
| `OPENAPI_RUNTIME_PARITY` | PASS | 76 runtime `(path, method)` entries exactly match `contracts/openapi.yaml`; regression test added. |
| `FRONTEND_BUILD` | PASS_WITH_WARNING | Vite build passed; existing 1.34 MB minified JS chunk warning remains. |
| `PLAYWRIGHT_E2E` | PASS | 8 tests passed, including V4/V5/V6 Guardian flows and TravelerTwin Control Tower evidence panel. |
| `COMPILEALL_RUFF` | PASS | Python compileall clean and Ruff clean over app/tests. |

## Known external limitations

- Hermes CLI could not complete because the isolated official installer could not obtain its GitHub repository. Native DeepSeek and checked-in MCP V2/Gateway paths remain separately verified.
- Overpass returned no results in the fresh bounded capture; this is preserved as `NO_RESULTS`, with Nominatim fallback candidates and no fabricated Overpass data.
- Phoenix export is optional and not configured in this run.
