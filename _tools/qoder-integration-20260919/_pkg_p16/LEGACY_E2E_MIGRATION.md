# Legacy E2E migration map — the eight `/` Journey Mode specs

Arbiter's ruling (pass-8, §4): do **not** swap `journey-status` for some V8
testid and call the migration done — "that is just resurrecting a selector
corpse". Archive each legacy spec only after its *capability invariant* has been
shown to exist in the current suite, and record the mapping either way.

## Why all eight fail identically

`src/main.tsx`'s `App()` renders `V8Experience` for every route and only falls
back to `LegacyApp` when the path starts with `/legacy`. The old Journey Mode
surface still exists — it was deliberately moved behind that path ("a first-time
user never lands on the legacy surface, see PHASE 2"). Each of the eight starts
with `page.goto("/")` and asserts `data-testid="journey-status"`, which only the
legacy tree renders.

Probe (temporary, reverted): pointing `golden.spec.ts` at `/legacy` made
`journey-status` resolve immediately, with `data-source="backend"` already
satisfied; the next assertion then failed on `ACTIVE` vs the real
`PLANNED · backend truth`. So the entry path is one line, and the remaining gap
is a truth-value question, not a dead surface.

## The map

| legacy spec | capability invariant it actually guards | current equivalent | status | decision |
|---|---|---|---|---|
| `golden.spec.ts` | journey state comes from backend truth, and a closure event triggers recovery that survives reload | `backend/tests/test_guardian_v4.py`, `test_impact_resolver.py`; frontend `qoder-ack-resolution.spec.ts` (ack vs resolution, self-seeded) | covered at API + rendered level | **Archive** once `/legacy` entry is recorded; keep the reload-persistence case by porting it onto the V8 Live surface |
| `live-autopilot-v5.spec.ts` | zero-touch autopilot: provider pulse → CP-SAT V2 → recovery → reload | `test_solver_v2_integration.py`, `test_solver_runtime_gate.py`, `test_agent_mission_runtime.py`; `qoder-live-structure.spec.ts` L1→L2→L3 state matrix | recovery chain covered server-side; the *zero-touch* UI trigger is not | **Port first**: needs a V8-level test that the autopilot fires without a user prompt |
| `predictive-real-city-v6.spec.ts` | predictive real-city twin prevents a weakness before it bites | `test_v13_3_real_city_intelligence.py`, `v13-5-fully-grounded.spec.ts` (fully grounded discovery, passing) | partially covered — detection yes, autonomous prevention no | **Port first** |
| `product-hardening.spec.ts:10` | TravelerTwin Control Tower renders persisted evidence and an explicit authority boundary | `test_gpt_agent_authority_v3.py`, `test_gpt_v5_mission_authority.py` | authority boundary covered server-side; the Control Tower UI is legacy-only | **Archive** the UI expectations, keep the authority assertions |
| `product-hardening.spec.ts:21` | Control Tower compiles and reloads a persisted natural-language mission | `test_agent_mission_runtime.py`, `test_gpt_v5_mission_authority.py` | covered at runtime level, not through a UI | **Archive** with a note that no current UI owns this surface |
| `product-hardening.spec.ts:46` | assisted acceptance is policy-driven; route/feed evidence survives reload | `qoder-ack-rendered.spec.ts`, `qoder-ack-resolution.spec.ts`, `test_qoder_live_replans_endpoint.py` | covered, and covered *in the current product surface* | **Archive** |
| `product-hardening.spec.ts:172` | autonomous mode executes an envelope-safe recovery through the Agent Gateway | `test_gpt_agent_authority_v3.py`, `test_agent_runtime_gate.py` | gateway + envelope safety covered server-side | **Port first** if the V8 shell is meant to expose autonomous mode; otherwise archive |
| `product-hardening.spec.ts:251` | Proactive Guardian launches the flagship recovery without a new chat prompt | `test_guardian_v4.py`, `test_guardian_model_evidence.py`, `test_v10_flagship_e2e.py` | covered | **Archive** |

## Rules applied

- An invariant is "covered" only when something in the **current** suite asserts
  it against the **current** surface or API — not when a similarly-named old test
  exists.
- Where the capability is real but only the legacy UI asserted it visually, the
  decision is *port first, then archive*, so retiring the file never deletes a
  behaviour check.
- The four current-product specs (`product-v8` ×2, `real-world-trip-operations-v9`,
  `v10-live-execution`) are **not** in this file's archive list. Per the same
  ruling they stay in the default suite and get rewritten against today's V8
  behaviour; work so far: locale pinned (they assert English copy while the app
  follows `navigator.language`), the retired `hub.title` heading replaced by
  `today-heading`, `AI` → `Copilot`, `read-only ready` → the current
  `exec.readOnlyReady` value `available offline`, the hard-coded four offer cards
  turned into a logged branch, and the AgentComposer testid replaced by the
  Copilot dock.
- Correction (pass-11 disproved the original note in this file, which claimed
  those v10 specs "pass alone but fail in the serial full run because the suite
  shares one SQLite file"). That hypothesis is **false** and the database has
  been cleared of it: re-running the failing specs individually on the same HEAD
  and the same seed reproduced the identical failures. The real causes are
  contract drift and unfinished fixture ownership —
  `v10-live-execution` was simply the last spec of the family not yet owning its
  journey (fixed in pass-12 A), `product-v8` drives a Copilot submit control that
  has since changed shape, and `real-world-trip-operations-v9` drives the raw
  JSON workbench that is now deliberately hidden behind an Advanced/developer
  disclosure while `JourneyInboxWorkbench` is the consumer path. No reordering,
  no retries, and no database-harness change is warranted; the arbiter closed
  `TEST_INFRA_SHARED_DB_BLOCKER` and marked `PER_WORKER_TEMP_DB` as
  NOT_AUTHORIZED.

## pass-14: the four pure archives are actually archived

The arbiter's condition on archiving (pass-14 dispatch, §D): moving a file and
leaving it inside the default suite is a reorganisation, not a retirement.  So:

- `frontend/e2e/legacy/archived-product-hardening.spec.ts` holds the four cases, and
  drives `/legacy` — the only place that surface renders now (`src/main.tsx` falls back
  to `LegacyApp` only for paths starting with `/legacy`).
- `frontend/playwright.config.ts` sets `testIgnore: /[\/]e2e[\/]legacy[\/]/`, so an
  acceptance run cannot discover them.
- `frontend/playwright.legacy.config.ts` runs them on explicit request and refuses to
  become authoritative; its results are non-gating by construction.
- No assertion was weakened or skipped during the move.  Run for real on 2026-09-19
  with `npx playwright test --config playwright.legacy.config.ts` against a
  self-started backend: **4 passed (18.8s)**.  That is the evidence for what this
  document has claimed since pass-8 — the surface is alive under `/legacy`, and the
  only reason these four were red inside the current suite is that they asked the
  root path for it.  Being green here changes nothing about gating: this config
  cannot be made authoritative, and these results do not count toward a merge gate.

Per-case record required by the ruling:

| archived case | capability invariant | why the old UI expectation is legacy-only | current owner (API / surface) | current coverage | archive location |
|---|---|---|---|---|---|
| TravelerTwin Control Tower evidence + authority boundary | persisted twin evidence is inspectable, and learned preferences are a *soft input* that cannot authorise actions | the TravelerTwin panel with `data-testid=traveler-twin-*` exists only in the legacy tree; V8 has no Control Tower surface | `GET /api/v1/journeys/{journey_id}/twin`, agent authority checks in `app/integrations/agent_gateway` | `backend/tests/test_gpt_agent_authority_v3.py`, `test_gpt_v5_mission_authority.py` (authority boundary, not the panel) | `e2e/legacy/archived-product-hardening.spec.ts` |
| Control Tower compiles and reloads a persisted NL mission | a natural-language mission compiles to codes + protected activity ids and survives reload | the mission composer (`agent-command`, `run-agent-command`) is legacy-only; V8's Copilot is a different surface with a different contract | `POST /api/v1/journeys/{id}/agent/commands`, persisted mission + run trace | `backend/tests/test_agent_mission_runtime.py`, `test_gpt_v5_mission_authority.py` | same |
| Assisted acceptance is policy-driven; route/feed evidence survive reload | a replan under ASSISTED requires confirmation, the approval receipt is consumed exactly once, and route evidence is provider-backed | the legacy event simulator / accept button and `.maplibre-container` route layers are not part of V8's acknowledgement flow | `POST /agent/tools/request_replan`, `/accept_replan`, `POST /agent/approvals/{id}`, `GET /route-evidence` | covered **in the current surface**: `frontend/e2e/qoder-ack-rendered.spec.ts`, `qoder-ack-resolution.spec.ts`, `backend/tests/test_qoder_live_replans_endpoint.py` | same |
| Proactive Guardian launches the flagship recovery without a new chat prompt | a standing mission plus a scan can recover the flagship leg with CP-SAT V2 evidence, without the traveller asking | the Guardian console (`guardian-flagship-scan`, `guardian-decision`, `guardian-trace`) lives in the legacy tree | `PUT /guardian/mission`, `POST /guardian/scan`, solver `ORTOOLS_CP_SAT_V2` | `backend/tests/test_guardian_v4.py`, `test_guardian_model_evidence.py`, `test_v10_flagship_e2e.py` | same |

Those four Port-first verdicts were executed, not re-litigated: pass-15 re-expressed
`golden.spec.ts`, `live-autopilot-v5.spec.ts` and the Agent-Gateway envelope case in
`product-hardening.spec.ts` on the current V8 surface, and pass-16 gave
`predictive-real-city-v6.spec.ts` a current owner (`V14PreventivePanel` on
`/v8/authoritative`).  All four pass in the authoritative acceptance suite, which
therefore has **no known-red case**; the table above is the historical judgement each
was archived or ported under, kept as the record of why.

What each one now asserts on the current surface, briefly: golden — accepted closure
recovery is backend truth, survives reload, and the browser never held the plan;
live-autopilot-v5 — the plan changes with no click or fill at all, and the audit feed
names the actor as `AI_AGENT`; product-hardening — an AUTONOMOUS envelope executes the
recovery and the panel shows the child version; predictive-real-city-v6 — a forecast
alone produces `PREEMPTIVE_RECOVERY` before any hard failure, with the run's evidence
rendered field by field.

One measured caveat about the *archived* set: with a real `DEEPSEEK_API_KEY` present,
the Proactive Guardian case is non-deterministic, because its flagship scan goes
through the model and the model may return no mutation
(`action_status = MODEL_NO_MUTATION`, where the assertion wants `EXECUTED`).  Measured
on the same tree: 4 passed with the AI switch disabled, 3 passed / 1 failed with the
host key inherited.  That suite is non-gating in any case, but its numbers must always
be quoted together with the AI switch state.
