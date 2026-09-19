# V12 Gate Matrix

| Required label | Status | Evidence |
| --- | --- | --- |
| `FROZEN_PROVIDER_EVIDENCE` | PASS | PlanVersion fields, persisted evidence, V12 evidence docs, same-candidate mutation test |
| `SAME_EVIDENCE_SELECT_GATE` | PASS | Selection reads stored evidence; full backend and V12 tests pass |
| `AUTHORITATIVE_MULTIDAY_COMPOSE` | PASS | CP-SAT bounded six-POI/three-day/two-night Top-K composition |
| `STAY_RESERVATION_ANCHORS` | PASS | Stay offer, check-in/out, arrival/departure, and imported C4 are planner inputs |
| `MONEY_EVIDENCE` | PASS | UNKNOWN/KNOWN/ESTIMATED status fields and full money regression coverage |
| `LIVE_EXECUTION_STATE_MACHINE` | PASS | Actual transition endpoints, timestamps, outcome events, NOW/NEXT |
| `UNIFIED_EXECUTION_TRUTH` | PASS | JourneyTwin, offline snapshot, and PIC Edge read the same active plan/execution state |
| `DND_PREVIEW_REPLAN` | PASS | Draft-only dnd-kit reorder, deterministic impact preview, accept creates new PlanVersion |
| `TYPED_FRONTEND_CLIENT` | PASS | OpenAPI-generated client and TanStack Query V12 hooks |
| `STORYBOOK_STATE_SYSTEM` | PASS | MSW-backed V12 primitives/state stories; Storybook build passes |
| `MAPLIBRE_RESIZE` | PASS | ResizeObserver/map.resize lifecycle plus desktop/mobile canvas probe |
| `SOURCEFUL_WEB_RUNTIME` | PARTIAL | SearXNG/DeepSeek source contract and NOT_CONFIGURED semantics present; live endpoint not configured |
| `LIVE_AGENT_MACHINE_EVIDENCE` | PARTIAL | Real DeepSeek proposal + redacted Gateway ALLOW_AUTO execution recorded; pure model-side accept continuation was not observed in the latest V12 bridge |
| `V12_FLAGSHIP_E2E` | PASS | Backend composition/execution/studio/autonomous recovery and browser preview/accept/reload proof |
| `21ST_EXTERNAL_ADOPTION` | NOT_RUN_EXTERNAL | 21st capability unavailable; no source adopted without provenance |

## Regression totals

- `pytest -q`: 347 passed, 2 skipped, 2 warnings.
- V12/V8/V10 focused: 9 passed, 2 warnings.
- `npm run build`: PASS.
- `npm run storybook:build`: PASS.
- `npm run test:e2e -- --reporter=line`: 15 passed.
