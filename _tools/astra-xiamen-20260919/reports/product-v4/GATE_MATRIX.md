# V4 Gate Matrix

| Gate | Result | Evidence |
|---|---|---|
| V4-01 Chinese numeric semantics | PASS | `test_v4_01_mission_budget_understands_chinese_numerals` and persisted standing Mission browser flow |
| V4-02 protected vs mutable polarity | PASS | `test_v4_02_protection_parser_respects_user_negation`; clause-local resolver |
| V4-03 real CP-SAT V2 | PASS | `ORTOOLS_CP_SAT_V2` provenance in unit, integration, Guardian, and browser tests |
| V4-04 native deterministic fallback | PASS | Enumeration remains bounded and labeled `CITYNEXUS_SOLVER_V2_ENUMERATION`; Mission compiler fallback is persisted |
| V4-05 Hermes when available | NOT RUN — EXTERNAL | Hermes endpoint, credential, and CLI were absent; adapter and primary-selection seam are implemented |
| V4-06 MCP V2 action surface | PASS | Full backend + MCP suite passed; all eleven allowlisted tools remain available |
| V4-07 RapidFuzz/Shapely with server ownership | PASS | Libraries installed and exercised by impact suite; unknown/terminal/C4 ownership checks remain authoritative |
| V4-08 quiet `NO_ACTION` | PASS | `test_guardian_no_action_is_quiet_and_deduplicated` |
| V4-09 one recovery per incident | PASS | Weather + traffic incident-set dedup in backend and flagship E2E |
| V4-10 in-envelope autonomous action | PASS | `test_guardian_flagship_executes_once_and_survives_reload` and Playwright flagship |
| V4-11 protected/C4 survives | PASS | Guardian protected-activity negative, existing C4 solver/gateway gates, Playwright cruise/dinner assertions |
| V4-12 over-budget confirmation | PASS | Guardian mission-envelope test plus existing Agent policy cost gate |
| V4-13 reload Guardian/Agent/Plan | PASS | Guardian status API test and browser reload assertion |
| V4-14 UI provenance layers | PASS | Journey Operations renders observation/inference/solver/policy/mutation lanes from persisted evidence |
| V4-15 offline golden regression | PASS | `321 passed, 2 skipped`; frontend `5 passed` |
| V4-16 secret/fresh package hygiene | PASS | Source secret scan clean; final archive extracted and focused replay completed |

## Runtime truth labels

| Capability | Status |
|---|---|
| `NATIVE_DEEPSEEK_MODEL_BACKED` | `NOT_RUN_NO_CREDENTIAL` |
| `HERMES_MODEL_BACKED` | `NOT_RUN_NOT_AVAILABLE` |
| `ORTOOLS_CP_SAT_V2` | `PASS` |
| `GUARDIAN_E2E` | `PASS` |
| `LIVE_VALHALLA` | `NOT_RUN_NOT_CONFIGURED` |
| `PHOENIX` | `NOT_RUN_NOT_INSTALLED_OPTIONAL` |
| `PROMPTFOO` | `NOT_RUN_NOT_INSTALLED_OPTIONAL` |
