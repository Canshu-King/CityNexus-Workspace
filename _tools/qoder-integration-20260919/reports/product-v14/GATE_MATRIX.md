# V14 Gate Matrix

| Gate | Evidence | Result |
|---|---|---|
| V14-01 initial grounded mobility | Fully grounded compose and selected-plan assertions | PASS; synthetic count `0` |
| V14-02 closure recovery | `backend/tests/test_v14_grounded_adaptive_recovery.py` | PASS |
| V14-03 provider reserve identity | Reserve-backed Place identity in recovery candidates | PASS |
| V14-04 departure boundary | C4 departure binds to activity `END` | PASS |
| V14-05 C4 protection | Haihe Cruise C4 preserved through recovery | PASS |
| V14-06 baseline immutability | Separate baseline and incident evidence | PASS |
| V14-07 incident provenance | Incident/event/provider observation IDs persisted | PASS |
| V14-08 weather capture | Sealed Open-Meteo forecast deterioration replay | PASS |
| V14-09 no fake live claim | No live traffic claim without capability | PASS |
| V14-10 Valhalla capability | `/status` probe implemented before live capture | PASS; live endpoint not configured |
| V14-11 traffic evidence | Event-time matrix or explicit degraded label; no strict baseline reuse | PASS |
| V14-12 grounded alternatives | Recovery candidate pairs restricted to provider-grounded reserve | PASS |
| V14-13 zero-synthetic recovery | Strict Golden recovery mobility | PASS; synthetic/mock count `0` |
| V14-14 graceful degradation | Legacy unavailable-provider path labelled explicitly | PASS |
| V14-15 semantic impact | DeepSeek contract plus deterministic server target path | PASS; live key not configured |
| V14-16 model boundary | Model claims cannot authoritatively mutate facts | PASS |
| V14-17 deterministic gate | Hard constraints and provider facts verified server-side | PASS |
| V14-18 authorization | Existing delegation/policy response surfaced in UI | PASS |
| V14-19 idempotent accept | Idempotency-key acceptance path | PASS |
| V14-20 child lineage | Accepted recovery creates child PlanVersion | PASS |
| V14-21 execution | Arrival executed before disruption and recovery accepted | PASS |
| V14-22 JourneyTwin | Accepted PlanVersion is authoritative in Twin | PASS |
| V14-23 UI | Grounded recovery evidence panel | PASS |
| V14-24 map | Accepted activity truth remains available to map surface | PASS |
| V14-25 offline | Service-worker/Dexie read-only reload | PASS |
| V14-26 backend vertical | Focused and broad backend runs | PASS |
| V14-27 browser Golden | Playwright V14 flow | PASS |
| V14-28 broad regression | Backend convergence run | PASS |
| V14-29 fresh extract | Final ZIP targeted runtime gate | PASS after packaging |
| V14-30 reporting | Reports and evidence included | PASS |

