# V13 Gate Matrix

| Gate | Result | Evidence / limitation |
| --- | --- | --- |
| Server-owned execution transitions | **PROVEN** | V13 illegal/repeated/backward/terminal/wrong-plan tests |
| Frozen evidence replay and tamper rejection | **PROVEN** | Hash, expiry, missing-pair and mutated-row tests |
| Shared authoritative Trip Studio feasibility | **PROVEN** | Preview and accept call the same deterministic gate |
| Active Journey progress preservation | **PROVEN** | Completed prefix/current pointer/timestamps survive edit |
| Truthful duration/cost/mode materialization | **PROVEN** | Frozen leg evidence and double-count regression |
| Mid-trip C4 anchor creation and binding | **PROVEN** | Real Inbox import/confirm API plus compose |
| C4 protection during autonomous recovery | **PROVEN locally** | Protected Commitment remains active; no automatic commitment management |
| Provider/replay → Event → Guardian → Gateway → mutation | **PROVEN locally** | V13 Golden recovery test |
| JourneyTwin/offline convergence | **PROVEN locally** | API, Twin, offline snapshot and Playwright |
| Idempotent no-op/retry behavior | **PROVEN locally** | No-op/repeated/concurrent accept; retryable Guardian finalization; worker-drain and full browser double-repeat stress |
| Sealed real-city evidence | **PROVEN as replay** | Tianjin Nominatim/Valhalla/Open-Meteo capture; Overpass no-results explicit |
| V13 composer live provider matrix | **PARTIAL** | Golden composer uses labelled `SYNTHETIC_FIXTURE`; no live network dependency |
| DeepSeek model-backed semantic path | **EXTERNAL / NOT CONFIGURED** | No key in process; native fallback remains available |
| Hermes orchestration endpoint | **EXTERNAL / NOT CONFIGURED** | No Hermes URL/key in process; MCP tests pass locally |
| Phoenix/OpenInference external export | **PARTIAL / NOT CONFIGURED** | Local OpenInference-shaped evidence exists; no external collector configured |
| Promptfoo literal CLI/model run | **PARTIAL** | Local deterministic adapter is `13/13`; Promptfoo CLI/model provider not configured |
| OpenAPI/type parity | **PROVEN** | 119 formal vs 119 runtime, no missing/extra |
| Accessibility/mobile/offline browser coverage | **PROVEN locally** | Full Playwright 16/16 includes accessibility, mobile and offline paths |
| Package/fresh-extract replay | **PROVEN** | `CityNexus-V13-Authoritative-Integrity-Commitment-Recovery-20260913.zip`; 318-entry archive; fresh extraction and compile validation at `D:\moodle\_v13_fresh_extract_20260913_final` |

The matrix intentionally separates product correctness proven by deterministic
local evidence from external integrations that were not configured. No secret,
database, cache, build output, nested archive or API key belongs in the final
review archive.
