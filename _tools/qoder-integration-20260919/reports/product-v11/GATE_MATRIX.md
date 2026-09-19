# V11 Gate Matrix

| Gate | Result | Evidence |
|---|---|---|
| REAL_DEEPSEEK_TOOL_AGENT | PASS | `LIVE_AGENT_EVIDENCE.md`, live Responses + domain mutation |
| PROVIDER_BACKED_COMPOSE | PASS (frozen replay/provider seam) | `PROVIDER_COMPOSE_EVIDENCE.md` |
| FROZEN_EVIDENCE_SELECT_GATE | PASS | 344 backend tests |
| LEG_LEVEL_PROVENANCE | PASS | MobilitySnapshot facts and replay tests |
| MONEY_EVIDENCE | PASS | existing money/authority regression |
| EXECUTION_RUNTIME | PASS | `EXECUTION_RUNTIME_EVIDENCE.md` |
| EDGE_ACTUAL_TIME | PASS | scoped backend/frontend execution tests |
| OFFLINE_ACTUAL_TIME | PASS | offline projection tests |
| SOURCEFUL_WEB_SEARCH | PARTIAL_EXTERNAL | optional SearXNG adapter; no configured endpoint |
| OPENAPI_TYPED_CLIENT | PASS | generated operation-derived ExecutionClock |
| TANSTACK_QUERY | PASS | typed execution/evidence hooks |
| DND_TRIP_STUDIO | PASS | dnd-kit draft reorder component |
| STORYBOOK_DESIGN_SYSTEM | PASS | Storybook build |
| UI_STATE_ACCEPTANCE | PARTIAL | 14/15 frontend E2E; one V6 reload follow-up |
| DEEPSEEK_VISUAL_REVIEW | PARTIAL_EXTERNAL | no new external critique run |
| OPENING_HOURS_TRUTH | PASS | preserved existing normalized semantics |
| GTFS_VALIDATION | NOT_CONFIGURED_EXTERNAL | no configured real GTFS feed |
| V11_FLAGSHIP_E2E | PASS | live model-selected tools → Gateway → accepted replan → persisted mutation; V5/V8/V9/V10 browser flows green |

External labels are not upgraded from replay or unavailable provider state.
