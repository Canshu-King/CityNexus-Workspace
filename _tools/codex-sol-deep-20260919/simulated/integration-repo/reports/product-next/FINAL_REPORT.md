# CityNexus Product Hardening — Final Report

Date: 2026-09-11  
Project: `D:\moodle\CityNexus`  
Iteration baseline: `2026-09-11T12:48:38+08:00`  
Report status: **local gates green; Agent Authority V2 complete locally; external model/provider boundaries explicit**

## Executive result

The product-next hardening slice is complete for the locally verifiable path:

```text
city event / AI semantic hypothesis
  -> server-owned impact and Activity facts
  -> OR-Tools candidate generation
  -> deterministic post-action feasibility gate
  -> user-owned Delegation Policy + Autonomy Envelope
  -> Agent Gateway command
  -> persisted domain mutation and audit projection
  -> MapLibre route evidence + Reflect history
```

The current product direction is intentionally more autonomous than the
original TXT's blanket rule that every `AI_ONLY` result must require
confirmation. The later user direction governs that conflict: a server-known,
ordinary, reversible, no-loss, non-protected Activity may be selected from an
AI semantic hypothesis and auto-executed in `ASSISTED`/`AUTONOMOUS` mode when
the deterministic post-action gate and the user's Autonomy Envelope pass.
`AI_ONLY` is still not called `VALIDATED_IMPACT`, cannot establish domain
truth, and cannot bypass ownership, state, feasibility, Provider, loss,
Commitment, or policy checks.

## Maturity matrix

| Capability | Strongest demonstrated level | Honest boundary |
| --- | --- | --- |
| Journey / PlanVersion / Booking / Payment mock / Commitment / Twin | `FROZEN_PASS` | Deterministic local domain path is regression-tested; real commerce is not enabled. |
| AI impact lifecycle and corroboration | `E2E_VERIFIED` | `AI_HYPOTHESIS` → `STRUCTURALLY_ELIGIBLE` → `CORROBORATED` → `VALIDATED_IMPACT` is explicit. Live model evidence is not current. |
| AI-only semantic target handling | `E2E_VERIFIED` | Server-known safe targets can enter replanning and auto execution inside the envelope; arbitrary or malformed IDs are rejected. |
| Deterministic OR-Tools solver and feasibility gate | `FROZEN_PASS` | Gate validates the resulting Journey and business facts; it is not a natural-language semantic replacement. |
| Agent Principal / Delegation Policy / Autonomy Envelope | `E2E_VERIFIED` | Local configured-token/server-principal boundary is verified; production identity infrastructure is out of scope. |
| Agent Gateway | `E2E_VERIFIED` | Pinned V1 tools plus typed V2 Activity/Booking/Commitment actions are live. Gateway validates request facts and records decisions/audit. |
| MCP server | `MCP_CONNECTED` / `E2E_VERIFIED` | V1 remains pinned at six tools; a separate V2 builder exposes typed actions through the same server-owned gateway. |
| Hermes tool integration | `MCP_CONNECTED` | V1 discovery remains six tools; V2 typed schemas are unit-tested. Discovery is not a model-backed Journey Agent. |
| Hermes natural-language model loop | `SKIPPED_EXTERNAL_DEPENDENCY` | No current Hermes inference/model credential was configured, so no model call was attempted. |
| DeepSeek live semantic loop | `SKIPPED_EXTERNAL_DEPENDENCY` | No current DeepSeek credential was configured. The earlier overnight claim is historical and not reused here. |
| Agent-driven frontend | `E2E_VERIFIED` | Assisted confirmation and Autonomous envelope-safe `ALLOW_AUTO` both use the Agent Gateway; server decisions are rendered. |
| Authoritative Agent Activity Feed | `E2E_VERIFIED` | Feed is projected from persisted audit rows and survives reload. |
| MapLibre route rendering | `PROVIDER_BACKED` / `E2E_VERIFIED` | Old/new GeoJSON comes from frozen server route evidence backed by the local mock mobility Provider. Live Valhalla is not configured. |
| Golden recovery scenario | `E2E_VERIFIED` locally | Full local closure recovery, C4 preservation, policy decision, audit, route evidence, and reload pass. Live DeepSeek/Hermes steps remain partial. |
| History / Reflect | `BACKEND_CONNECTED` / `E2E_VERIFIED` | Plan chain, replans, Agent actions, disruptions, costs, and feedback hook are exposed. Actual per-Activity transition timestamps are not yet persisted. |
| Typed commerce/commitment action tools | `E2E_VERIFIED` locally | V2 exposes replacement, reschedule, booking, refundable cancellation, and commitment-change request tools. High-risk calls produce scoped approval receipts and do not auto-charge/refund or bypass protected Commitment policy. |

## P0–P6 completion

### P0 — Impact corroboration hardening: complete with updated autonomy semantics

- Lifecycle maturity and provenance are explicit in the impact contract.
- Server evidence, not candidate-supplied evidence, decides whether an
  Activity is known, owned by the Journey, non-terminal, and eligible.
- Prompt-injection markers, narrow explicit contradiction, hallucinated IDs,
  stale state, low confidence, and malformed provider output are covered.
- Structured place/time evidence can reach `VALIDATED_IMPACT`.
- A server-known AI-only semantic target remains `AI_ONLY` but may proceed as
  a candidate and may auto-execute when the user-owned envelope and
  deterministic post-action gate pass.
- This is the deliberate implementation of the later product-direction
  instruction; the older TXT's AI-only blanket confirmation rule is not the
  governing policy for this run.

The archive-defined AAV2 regression is now **5/5 PASS**, plus a receipt
consumption test. AI-only retry cannot self-escalate, raw Event truth remains
unchanged, AI-only candidates stay out of `validated_activity_ids_json`, and
ADVISORY Commitment mutation cannot return `ALLOW_AUTO`.

### P1 — Hermes: protocol complete, model-backed loop partial

The real MCP SDK stdio server runs and Hermes Agent `0.19.0` connected to the
pinned V1 surface, discovering exactly six whitelisted tools. A separate V2
MCP builder now exposes typed Activity/Booking/Commitment commands, all routed
through the same server-owned principal and Gateway. Hermes has no terminal,
filesystem, arbitrary browser, raw database, payment, refund, or raw SQL
capability.

The external inference loop is not claimed complete. Current environment
checks found no configured DeepSeek/Hermes model credentials; the live model
path was skipped without attempting a network model call. No secret is present
in source, reports, logs, or the checkpoint.

### P2 — Agent-policy-driven frontend: complete

Assisted and Autonomous automated acceptance use
`/agent/tools/accept_replan`. The server returns `ALLOW_AUTO`,
`REQUIRE_CONFIRMATION`, `REQUIRE_STEP_UP`, or `DENY`; React does not invent the
decision. The UI includes the Autonomy Envelope controls and displays the
server decision and reason context.

Confirmation is now a server-issued approval receipt. The UI first receives a
pending receipt, calls the user approval endpoint, then retries the exact Agent
action with `approval_id`; the compatibility `user_confirmed` boolean is not
trusted.

### P3 — Authoritative Feed: complete

Gateway request, replan, impact, solver, policy, provider, confirmation, and
acceptance facts are written to the audit store and projected through
`/journeys/{journey_id}/agent-feed`. The projection includes actor, tool,
Journey, proposal, decision, reason codes, trace, and facts. Reload coverage
confirms the Feed is restored from the backend.

### P4 — Provider-backed MapLibre: complete for frozen local evidence

Route geometry is frozen outside the GET projection and returned by the route
evidence endpoint. MapLibre registers distinct baseline/proposed sources and
layers, activity/C4/disruption markers, and explicit Provider/fallback labels.
The browser test compares backend geometry with MapLibre source geometry and
checks feature counts and layer existence. A live Valhalla endpoint is not
configured in this environment.

### P5 — Autonomous recovery Golden: complete locally, model/provider partial

The serial backend-connected Playwright suite proves reset/bootstrap, booking
and capture mock, Journey activation/progress, closure injection, Agent replan,
envelope-safe Autonomous `ALLOW_AUTO`, active PlanVersion promotion, protected
C4 preservation, persisted audit Feed, frozen old/new route evidence, Reflect
summary, and full reload recovery. Assisted confirmation is also covered.

The browser scenario uses the deterministic local closure/mock Provider. It
does not claim a live DeepSeek → Hermes natural-language model loop because
the external credentials are absent.

### P6 — History / Reflect: complete at minimum scope

`/journeys/{journey_id}/reflect` and the frontend history card expose completed
state, planned timeline, Replan history, Agent action history, Provider
disruptions, cost summary, PlanVersion chain, and a user-only preference
feedback hook. The response explicitly reports that actual transition
timestamps are unavailable rather than fabricating them.

## Verification evidence

All commands below were run against the current working tree, not inferred
from an old report.

| Check | Result |
| --- | --- |
| Backend full regression | `294 passed, 2 skipped, 2 warnings` |
| AAV2 authority + receipt + typed V2 actions | `9 passed, 2 warnings` |
| Focused impact regression | `17 passed, 2 warnings` |
| Agent runtime regression | `21 passed, 2 warnings` |
| Backend compileall | PASS |
| Ruff check | PASS |
| Ruff format check | PASS |
| OpenAPI formal/runtime parity | `50 / 50`, missing `0`, extra `0` |
| MCP V1/V2 SDK/unit + real V1 stdio protocol tests | `5 passed` |
| Frontend production build | PASS; Vite emitted only the existing large-chunk warning (1,320.88 kB JS) |
| Backend-connected Playwright | `3 passed` with one worker; shared local SQLite is intentionally serialized |
| Isolated Hermes probe | Agent `0.19.0`, six tools discovered, `hermes mcp test citynexus` PASS |
| Targeted credential hygiene | PASS: no credential-shaped assignment in repository text; current model credential variables absent |

The two documented backend skips are the optional “simulate missing OR-Tools”
boundary (OR-Tools is installed) and live Valhalla smoke (URL is not
configured). The deterministic OR-Tools runtime tests themselves pass.

## Changed product surface

- Impact contract/validation/resolution now carries maturity, lifecycle path,
  authoritative evidence, provenance, and rejection reasons.
- Policy persistence/API/UI now carries the Autonomy Envelope: maximum cost
  increase, maximum loss, schedule drift, allowed Activity types, protected
  Commitment levels, and pre-authorized Commitment management.
- Agent Gateway derives acceptance facts from server state, applies policy,
  issues and consumes scoped approval receipts when required, and persists
  traceable audit events.
- Real MCP stdio server, tool catalog, Hermes config example, and principal
  boundary are documented and tested.
- Agent Feed, route evidence, MapLibre old/new routes, and Reflect are
  backend-connected and reloadable.
- Frontend policy writes are serialized and controlled inputs remain responsive
  while the authoritative PUT is in flight.
- OpenAPI contracts and runtime routes are kept in parity.

## Remaining partials and external blockers

1. A live DeepSeek semantic smoke and a Hermes model-backed natural-language
   loop need operator-supplied, process-only credentials and a reachable
   provider. They were intentionally not simulated.
2. Live Valhalla geometry needs `CITYNEXUS_LIVE_VALHALLA_URL`; local frozen
   mock mobility evidence is the verified Provider-backed path in this run.
3. The pinned V1 Gateway remains six tools, while the separate V2 surface now
   exposes typed replacement, reschedule, booking, refundable-cancel, and
   explicit higher-policy Commitment management commands. High-risk tools stay
   callable by an Agent and return Gateway outcomes such as confirmation or
   step-up when outside the envelope.
4. Actual start/end transition timestamps and persisted preference feedback are
   the next Reflect data-model increment.
5. The frontend bundle has a non-blocking MapLibre chunk-size warning.

## Fresh-extract replay

Fresh-extract replay: **PASS**.

Final checkpoint `CityNexus-Agent-Authority-V2-Final-20260911.zip` contains
2,214 files. Archive inspection found zero forbidden runtime/dependency,
history, or nested-ZIP entries and zero targeted credential-shaped assignments.
After extraction, compileall passed; the complete backend suite passed with
`294 passed, 2 skipped, 2 warnings`; MCP passed `5`; and OpenAPI parity passed
`50/50` with no missing or extra routes. Frontend build and serial Playwright
`3/3` were already verified against the same source tree; dependency folders
are intentionally excluded from the portable checkpoint.

## Next three highest-value actions

1. Configure an operator-owned DeepSeek/Hermes provider environment and run one
   fully traced natural-language recovery loop, preserving the same server
   gates and redacted audit rules.
2. Configure an operator-owned Hermes/DeepSeek provider environment and run one
   fully traced natural-language V2 action loop without weakening the same
   server gates.
3. Persist actual Activity transition timestamps and preference feedback, then
   add live Valhalla route-shape replay to close the remaining Reflect and
   Provider-backed gaps.
