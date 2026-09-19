# CityNexus V18.2 Native Hermes Agent Experience

Date: 2026-09-15

## Result

V18.2 productizes the existing native Hermes connection as a bounded, visible
multi-step travel-agent surface. DeepSeek remains the semantic compiler;
Hermes is used only for genuine replan/disruption missions; CityNexus remains
the source of facts, identifiers, provider evidence, feasibility, approvals,
and mutations.

The release artifact is:

`CityNexus-V18.2-Native-Hermes-Agent-Experience-20260915.zip`

## Delivered

- Added the explicit `citynexus.mission-plan.v1` envelope with ordered
  inspection, search, deterministic replan, proposal, and approval-boundary
  steps.
- Added a normalized, persisted runtime event contract with safe summaries,
  friendly tool labels, run observability, reconnect hydration, and no model
  chain-of-thought or credentials.
- Kept `EXPLAIN_PLAN`, simple `WHAT_IF`, preference explanations, and simple
  Journey lookups on DIRECT. Native Hermes is selected for replan and
  disruption missions only.
- Passed authoritative Journey and mission identifiers into the Hermes
  process, including the exact trigger event when a replan is actionable.
- Enforced `PLAN_ONLY` at the CityNexus Gateway/Guardian boundary. Hermes can
  inspect, search, simulate, and request a proposal; it cannot silently accept
  a replan, book, pay, or mutate a protected commitment.
- Added CityNexus-backed Approve, Reject, Modify/Review, and Stop controls.
- Reworked desktop and mobile Copilot rendering around the real ordered event
  history. The panel persists mission history across close/navigation, and raw
  runtime details are disclosure-only.
- Added the sealed Tianjin Golden scenario at
  `evals/v18_2/golden_hermes_tianjin.json`.

## Runtime truth

A real native Hermes run was observed with runtime identity
`HERMES_NATIVE_MCP` and actual CityNexus MCP calls; see
`HERMES_AGENT_EVIDENCE.md`. A later overnight smoke run was explicitly stopped
through the CityNexus proxy when the external DeepSeek endpoint was not
responding. That failure is rendered as a failed/cancelled run, never as a
successful Hermes mission.

No protected commitment, booking, payment, or PlanVersion mutation was
performed by the proof runs.

## Validation

The final backend regression was `425 passed, 2 skipped, 2 warnings`; the V18.2
and V18.1 native contract gates passed; and the frontend production build
completed successfully. Desktop and 390x844/430x932 mobile Playwright flows
exercised the Copilot panel, native run state, real event handling, and the
CityNexus Stop proxy.

The only external limitation recorded is two bounded DeepSeek Responses
connect timeouts for the reused Windows User-scope credential. The credential
value was never printed, persisted, or packaged.
