# V10 gate matrix

| Gate | Status | Evidence |
|---|---|---|
| DEEPSEEK_V41_FLASH | PARTIAL_EXTERNAL | Official text/web/vision HTTP 200; live function probe rejected thinking+forced tool choice |
| DEEPSEEK_RESPONSES_API | PASS | `backend/app/integrations/ai/responses.py`, response normalization tests |
| DEEPSEEK_WEB_SEARCH | PARTIAL_EXTERNAL | HTTP 200; no source observations exposed in the live response, no fabricated observation persisted |
| DEEPSEEK_VISION | PARTIAL_EXTERNAL | HTTP 200; structured image route and deterministic mocked flagship test pass |
| MULTIMODAL_JOURNEY_INBOX | PASS_REPLAY | Text/image drafts, field provenance, unresolved critical fields, confirmation route, UI workbench |
| ICS_MATURE_PARSER | PASS | `icalendar` parser and field-provenance test |
| QR_BARCODE_IMPORT | PASS | `@zxing/browser` scanner component and V10 Inbox E2E |
| PROVIDER_CAPTURE_TRUTH | PASS_REPLAY | Synthetic label correction, sealed checksum replay loader and tests |
| REAL_COMPOSE_ENGINE | PASS | Arbitrary explicit POI Compose Engine test, deterministic feasibility gate |
| EXECUTION_CLOCK | PASS | Freezeable clock and `/execution-clock` E2E |
| EDGE_RUNTIME_TRUTH | PASS | V9 Edge snapshot/actions and current-time projections remain green |
| OFFLINE_ACTUAL_NOW | PASS | V9 offline reload E2E and IndexedDB snapshot |
| OPENAPI_TYPESCRIPT | PASS | Generated `frontend/src/generated/api.ts` regenerated from contract |
| TANSTACK_QUERY | PASS | V10 ExecutionClock/WebObservation panel |
| STORYBOOK | PASS | Storybook 9.1.20 static build |
| UI_GITHUB_ADOPTION | PASS | 21st MCP search/inspection plus adoption ledger; no unlicensed source copied |
| DEEPSEEK_VISUAL_REVIEW | PARTIAL_EXTERNAL | Cycle 1 applied; cycle 2 strict JSON parse failed externally |
| AXE_ACCESSIBILITY | PASS | Zero violations on mobile Live Journey |
| LIGHTHOUSE_QUALITY | PASS_EQUIVALENT | Playwright performance/layout/console/5xx budget; Lighthouse CLI not run |
| REAL_WEB_PUSH | CONDITIONAL | VAPID/pywebpush path and push-config route; current default is record-only |
| OTP_TRANSIT | NOT_CONFIGURED | Provider status explicitly returns `UNKNOWN_REALTIME` / `NOT_CONFIGURED` |
| V10_FLAGSHIP_E2E | PASS_REPLAY_CONDITIONAL | Inbox→generic compose→web evidence→clock backend test plus 15-test browser regression |
| HERMES_MODEL_BACKED | NOT_CONFIGURED | Optional Hermes adapter and MCP V2 tools exist; no endpoint/key |

## Regression gate

V5 zero-touch Autopilot, V6 predictive recovery, V8 product experience, V9 real-world operations, V10 Inbox, V10 Live Execution, V10 accessibility, and V10 quality budget all passed in a fresh-process run.

