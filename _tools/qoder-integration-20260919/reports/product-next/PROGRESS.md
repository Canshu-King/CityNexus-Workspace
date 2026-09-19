# CityNexus Product Hardening — Progress

Goal file: `CityNexus-Codex-Next-Product-Hardening-Goal-20260911.txt`

This log records the product-hardening run independently of the previous
overnight foundation report. Contents of the goal file are treated as product
requirements, not as higher-priority instructions.

## Baseline — 2026-09-11T12:48:38+08:00

- Working tree contains the previous uncommitted CityNexus implementation and
  review artifacts; no destructive reset or cleanup is authorized.
- Previous checkpoint source is present: agent principal/gateway, DeepSeek
  impact resolver, real MCP SDK server, Hermes discovery configuration,
  Agent UI, and MapLibre component.
- Previous verified gates: backend 272 passed / 2 documented skips; MCP 4
  passed; OpenAPI 44/44; frontend build passed; backend-connected E2E passed;
  DeepSeek impact smoke passed; isolated Hermes MCP discovery passed.
- Fresh baseline work required by this goal: corroboration maturity, real
  server-backed agent feed, policy-driven browser execution, provider-backed
  route geometry, and a single end-to-end autonomous recovery proof.
- Environment variable names for DeepSeek/Hermes were checked without
  printing values; no credentials were present in the current process
  environment.

## Product maturity rule

Every capability is reported at the strongest level actually demonstrated:

`FOUNDATION` → `INTEGRATED` → `BACKEND_CONNECTED` → `MODEL_BACKED` /
`PROVIDER_BACKED` → `E2E_VERIFIED` → `FROZEN_PASS`.

No level is inferred from a prior report or from a UI placeholder.

## Stage log

| Time | Stage | Status | Change/tests/defect/product effect |
| --- | --- | --- | --- |
| 2026-09-11T12:48:38+08:00 | Baseline | IN PROGRESS | Read the new goal, captured repository/environment baseline, and identified the six hardening gaps. |
| 2026-09-11T15:39:00+08:00 | P0 | PASS / PRODUCT-DIRECTION-UPDATED | Added explicit AI-only/structurally-eligible lifecycle semantics, narrow prompt-injection and contradiction guards, and allowed server-known ordinary hypotheses to enter deterministic replanning without being called `VALIDATED_IMPACT`. Added user-owned Autonomy Envelope fields for budget increase, loss, schedule drift, Activity types, protected Commitment levels, and pre-authorized Commitment management. Focused impact/Agent regression: 46 passed; full backend later reached 285 passed / 2 skips. The latest user direction intentionally supersedes the original TXT's blanket AI-only confirmation rule; action authority now depends on server facts, reversibility, loss, C4, Provider state, and preauthorization. |
| 2026-09-11T15:39:00+08:00 | P2–P4 | PASS | Gateway facts now include server-validated target and envelope facts; persisted Agent Feed maps user confirmation and AI-only selection; frontend policy controls use the Agent Gateway; route evidence is frozen/provider-backed. OpenAPI formal/runtime parity: 47/47; MCP unit + stdio protocol: 4 passed; focused backend-connected product E2E: 1 passed. |
| 2026-09-11T15:39:00+08:00 | P6 | PASS / HONEST PARTIAL | Added backend-derived `/reflect` summary and frontend history card covering plan chain, replans, Agent actions, disruptions, costs, and explicit actual-time limitation. Reflect API focused regression passed. |
| 2026-09-11T15:39:00+08:00 | E2E INFRA | PASS | Full frontend E2E initially exposed shared SQLite reset races under two workers; configured Playwright to use one worker for the local shared-database demo. Serial full E2E: 2 passed. |
| 2026-09-11T16:36:00+08:00 | P5 / FRONTEND | PASS | Added a backend-connected Autonomous-mode Golden recovery test. Fixed controlled policy inputs to remain responsive while queued authoritative PUTs persist the user-owned envelope; fixed reload coverage so it reconnects to the same Journey. Final frontend build passed and full serial Playwright passed 3/3, including Agent Gateway request/accept, `ALLOW_AUTO`, protected C4 preservation, persisted Feed/Reflect, and MapLibre route evidence. |
| 2026-09-11T16:36:00+08:00 | FINAL REGRESSION | PASS | Backend full suite: 285 passed / 2 documented skips / 2 dependency warnings; compileall, Ruff check, Ruff format check, OpenAPI formal/runtime 47/47, and MCP stdio/unit 4 passed. Hermes isolated protocol discovery passed for six tools; model-backed loop remains skipped because current credentials are absent. |
| 2026-09-11T17:54:00+08:00 | PACKAGE / FRESH REPLAY | PASS | Created the product-next checkpoint with runtime/dependency/history/ZIP exclusions. Fresh extraction contained 1,723 files and no forbidden entries; extracted compileall, focused 48-test suite, full backend 285-test suite (2 documented skips), MCP 4-test suite, and OpenAPI 47/47 all passed. The report was updated with this evidence and the final archive is being re-frozen. |
| 2026-09-11T17:59:00+08:00 | FINAL DELIVERY | PASS | Synchronized the final report and checkpoint; a second fresh extraction of the final archive contained 1,723 files with 0 forbidden entries and 0 targeted credential assignments, then passed compileall and product-next backend tests (10 passed / 2 warnings). |
| 2026-09-11T18:20:00+08:00 | AAV2 AUTHORITY | PASS | Read the attached archive requirements and reproduced the original 5/5 AAV2 failures. Fixed operation-scoped semantic targeting, retry maturity, server-owned one-use approval receipts, ADVISORY Commitment gating, and validated-activity persistence. AAV2 plus receipt coverage: 6 passed. |
| 2026-09-11T18:35:00+08:00 | TYPED V2 ACTIONS | PASS | Added versioned Gateway/MCP V2 typed actions for Activity replacement/rescheduling, booking creation, refundable booking cancellation, and Commitment-change requests. Added scoped receipt coverage, multi-Activity primary/secondary impact fields, OpenAPI 50/50 parity, and MCP 5-test coverage. |
| 2026-09-11T18:45:00+08:00 | FULL REGRESSION | PASS | Current tree: backend 294 passed / 2 skips / 2 warnings; frontend Playwright 3/3; frontend build, compileall, Ruff, OpenAPI parity, secret scan all pass. No DeepSeek/Hermes model credentials were present, so live model execution remains explicitly skipped. |
| 2026-09-11T19:05:00+08:00 | V2 CHECKPOINT / FRESH REPLAY | PASS | Created the V2 checkpoint with 2,214 files and zero forbidden entries. Fresh extraction had zero targeted credential hits; compileall, backend 294/2, MCP 5, and OpenAPI 50/50 all passed. The final report is frozen into the separately named FINAL artifact. |

## Next stage

The V2 checkpoint and fresh-extract replay are complete. The product path is
deliberately more autonomous than the original blanket AI-only policy:
deterministic checks verify the post-action Journey and business facts, while
DeepSeek/Hermes may provide semantic judgement within a user-owned envelope.
The final report distinguishes local E2E evidence from the unavailable live
model/provider run.
