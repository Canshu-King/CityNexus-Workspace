# CityNexus — WP06 Post-Gate Review Follow-up for Codex

Date: 2026-09-09

## Decision

The WP06 post-gate **core is accepted**: lifecycle/idempotency hardening, Event provenance, Valhalla HTTP adapter, MobilitySnapshot boundary, deterministic F0/F1/F2 candidate generation, verified replan scoring infrastructure, and the 133-pass checkpoint baseline are credible.

However, do **not freeze the multi-candidate/scoring/JourneyTwin UI contract yet**. Apply the bounded fixes below in the current working tree, preserve all existing work, then continue forward.

## User rule

- No SHA/file/archive hash work.
- No rollback of accepted WP04/WP05/WP06 work.
- Do not delete Foundation/provider code to satisfy old tests.
- Keep real external providers optional; default tests/demo remain network-free.

---

## P0 — candidate_count must count feasible candidates, not raw candidate specs

### Reproduced defect

Current code slices:

```python
specs = specs[: body.candidate_count]
```

**before** authoritative feasibility gating.

Reproduction:
1. canonical Tech Art closure;
2. make the first-ranked Design Library unavailable at the affected time;
3. request `candidate_count=1`.

Observed:
- first raw F0 candidate fails with `PLACE_CLOSED`;
- API returns 422;
- a lower-ranked City Park candidate is feasible and appears if `candidate_count=3`.

This violates the existing contract:

> Generate up to `candidate_count` distinct **feasible** candidate plans.

### Required repair

Do not truncate raw specs before the gate.

Instead:
1. iterate deterministic candidate specs in rank order;
2. gate each candidate;
3. append only feasible candidates;
4. stop when `len(created) == body.candidate_count`;
5. if fewer feasible candidates exist, return the feasible subset;
6. return 422 only when zero feasible candidates exist.

Regression test:
- top replacement infeasible + lower replacement feasible + `candidate_count=1`
  -> 201 with the lower feasible candidate.

---

## P1 — make score metric names truthful

### Reproduced defect: `preference_fit`

Changing the Traveler's only positive interest preference between:

- `culture`
- `waterfront`
- `local_food`

produces exactly the same replan `preference_fit` and utility scores.

Current implementation computes replacement tags vs **affected place tags**, not Traveler Preference.

That is replacement similarity, not preference fit.

### Required repair

Before frontend/AI comparison freeze:

Preferred:
- derive `preference_fit` from persisted Traveler preferences and candidate Place tags.

If the correct verified input is not ready:
- use the documented neutral value;
- do not label affected-place similarity as `preference_fit`.

Do not ask an LLM to score it.

### Reproduced drift: `opportunity_value`

Current value is effectively based on replacement duration (`<=60 -> 1.0`, otherwise `0.5`) and is not derived from `OpportunityWindow`.

Required:
- compute it from real OpportunityWindow evidence, or
- use neutral/unavailable policy until that evidence is wired.

---

## P1 — F3 must be a real Opportunity Window family or be renamed

Current `F3_WINDOW_REPLACEMENT` is simply the second ranked same-slot closure replacement. It does not call OpportunityWindow fitting logic and does not actually create a distinct opportunity-window plan family.

Before exposing family names in the UI:

Either:
1. implement a real opportunity-window-compatible F3 candidate using current time, next protected commitment, travel, safety buffer, opening hours and budget;

or, if that is intentionally deferred:
2. rename it to an honest alternate same-slot replacement family and reserve F3 for the real Opportunity Window implementation.

Do not leave a misleading family label in the public comparison contract.

---

## P1 — JourneyTwin `upcoming_commitments` must not contain completed/past commitments

### Reproduced defect

Canonical River Cruise reaches C4, Journey starts, activities are completed through the cruise.

At `now=17:00`, JourneyTwin correctly has no next Opportunity Window for the 15:30 cruise, but:

```text
upcoming_commitments
```

still contains the C4 River Cruise with status `ACTIVE`.

### Required repair

At minimum, build `upcoming_commitments` as a projection:
- include current/future active commitments;
- exclude commitments whose linked Activity is terminal/past;
- for time-anchored commitments, use verified scheduled time;
- do not mutate domain truth merely to make the projection look right.

Separately, if the frozen Commitment state machine explicitly permits it, add the correct Activity-completion -> Commitment `FULFILLED` transition. Do not invent a transition if the source model says otherwise.

Regression test:
- after completing the C4 cruise, it must no longer appear under `upcoming_commitments`.

---

## P1 — make replan generation retry-safe before the frontend

### Reproduced behavior

Calling the same:

```text
POST /journeys/{journey}/replans
trigger_event_id = same event
candidate_count = 3
```

twice creates six PRESENTED proposals / six candidate PlanVersions.

Acceptance later invalidates siblings correctly, so this is not a hard correctness failure, but a browser retry/double-click can create duplicate candidate sets.

### Required repair before frontend freeze

Use one of these bounded policies:

Preferred:
- require an `Idempotency-Key` on replan generation, parallel to replan accept;
- same key + same request -> exact replay, no new PlanVersions;
- same key + different request -> 409.

Alternative:
- reuse an equivalent still-PRESENTED candidate set for the same event/base plan/request.

Do not make a generic distributed job system.

---

## P2 — deterministic tie-breaking

Current top proposal sort uses:

```python
(-utility_score, proposal.id)
```

`proposal.id` is UUID4, so exact score ties are not deterministic.

Use a deterministic family/rank/creation-order tiebreak instead. Python stable sort over deterministic candidate generation order is sufficient.

---

## P2 — test harness cleanup

The packaged Windows validation reports 133 passed + 1 skipped.

In an independent Linux/container replay, `python -m pytest` reaches the full progress output but may fail to exit cleanly; individual WP06/provider files terminate and pass. Multiple test modules create module-global `TestClient(app)` objects.

This is not a CityNexus functional gate, but before CI:
- prefer fixtures/context-managed TestClient;
- avoid module-global clients where practical.

Do not spend a full work cycle on this.

---

# Continue after the bounded repair

When the above P0/P1 contract fixes are green, continue without another architecture redesign:

1. Valhalla optional local/controlled smoke -> freeze facts into MobilitySnapshot;
2. Open-Meteo provider ingestion -> `PROVIDER_VERIFIED` server-side Event facts;
3. wire frozen mobility/context facts into replan evidence and FeasibilityEnvelope;
4. OR-Tools as optional advanced candidate generator behind the same gate;
5. LiteLLM + DeepSeek for explanation/recommendation only;
6. MapLibre + Turf + XState + shadcn/ui;
7. Playwright Golden Scenario.

Hard rules remain:
- CityNexus deterministic feasibility is authoritative;
- C4 Commitment is authoritative;
- raw network provider objects never enter the gate;
- AI never decides hard feasibility/payment/commitment truth;
- no external service becomes mandatory for default demo/tests.

## Next checkpoint evidence

Provide:
- previous 133 tests retained;
- new feasible-candidate-count regression;
- preference-fit evidence changes when Traveler preference changes, or explicit neutral policy test;
- real/renamed F3 semantics test;
- completed C4 absent from `upcoming_commitments`;
- replan generation retry/idempotency regression;
- deterministic tie-break regression;
- no-live-network default path still green.
