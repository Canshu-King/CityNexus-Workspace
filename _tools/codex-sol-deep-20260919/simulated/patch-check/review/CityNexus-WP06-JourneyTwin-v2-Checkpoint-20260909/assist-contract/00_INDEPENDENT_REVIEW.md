# CityNexus Post-WP04 Foundation Checkpoint — Independent Deep Review

Date: 2026-09-09

## Review rule

No SHA/file/archive hash checking was performed. Hash work should remain excluded from future Codex review tasks.

## Reproduction result

The checkpoint reports 104 passing backend/foundation/hardening/WP05 tests. The package is a delta-style checkpoint rather than a directly runnable full repository, so the current implementation was reconstructed from the last full repo-relative checkpoint plus the WP04 checkpoint and this delta. On that reconstructed working tree:

```text
104 passed
Python imports/compile: PASS
```

The reported 104-pass result is therefore independently reproducible.

## What is genuinely implemented

- WP04 hardening is present: per-connection SQLite FK enforcement, booking service/slot binding, duplicate active-booking guard, semantic duplicate-capture guard.
- WP05 start/complete/history/event endpoints exist.
- JourneyTwin ORM/API projection exists.
- ReplanProposal persistence/API exists.
- ReplanDiff is persisted and exposed.
- deterministic fallback Copilot exists.
- provider/AI/mobility/discovery/trust/OR-Tools foundation modules are installed but mostly not wired into runtime yet, which is appropriate for staged rollout.

## Important defects found beyond the 104 tests

### P0 — JourneyTwin response was not durably persisted on start/complete

`start_journey()` and `complete_activity()` committed the Journey changes first, then called `_twin_snapshot()`. `_twin_snapshot()` flushed a JourneyTwin row but no later commit occurred, so the request returned a Twin that was rolled back when the session closed.

Independent reproduction:

```text
POST /start -> 200 Twin returned
DB JourneyTwin after request -> missing
POST /activities/{id}/complete -> 200 Twin returned
DB JourneyTwin after request -> still missing
```

### P0 — ACTIVE Journey mutations bypassed feasibility protection

`validate_selected_plan_feasibility()` only guarded `PLANNED + SELECTED`. After WP05 moved a Journey to `ACTIVE + ACTIVE`, the same PATCH/constraint endpoints stopped revalidating.

Independent reproduction:

```text
ACTIVE Journey
PATCH budget to 1 CNY -> 200
add HARD BUDGET_MAX=1 -> 201
```

The active Journey could therefore become internally infeasible without entering Replanning.

### P0 — Replanning was allowed before Journey start

A `PLANNED` Journey could generate and accept a replan. Acceptance produced:

```text
Journey.status = PLANNED
new PlanVersion.status = ACTIVE
```

This violates the declared lifecycle.

### P0 — cross-Journey Event could trigger another Journey's replan

The old check verified only that the Event existed, not that `Event.journey_id == Journey.id`.

### P0 — accepted replan left `current_activity_id` on the superseded plan

The new PlanVersion contains new Activity IDs. After acceptance, `Journey.active_plan_version_id` pointed to the new plan but `Journey.current_activity_id` still pointed to an Activity from the old plan.

### P0 — durable C4 Commitment facts were not fed into Replan feasibility

WP04 stores the canonical C4 anchor in `Commitment.policy_json` using a stable semantic key + scheduled time. The shared feasibility gate only consumed JourneyConstraint `LOCKED_COMMITMENT` records. A future replan could therefore pass the gate without proving that a commerce-created C4 Commitment survived.

### P1 — Replan state machine drift

The declared state machine is:

```text
GENERATED -> PRESENTED -> ACCEPTED/REJECTED
```

The runtime accepted `GENERATED` directly. For a synchronous API that returns the proposal to the caller, the clean MVP rule is to persist it as `PRESENTED` before returning it, then accept/reject only `PRESENTED`.

### P1 — current checkpoint packaging is not directly runnable

Several changed files are exported at flattened paths such as:

```text
implementation/backend/app/models.py
implementation/backend/app/session.py
implementation/backend/app/service_impl.py
```

while the actual imports are `app.db.models`, `app.db.session`, `app.commerce.service_impl`, etc. The package can be reviewed as a delta, but future checkpoints should preserve exact repo-relative target paths or include an explicit overlay mapping.

### Architectural blocker for real mobility

The authoritative feasibility gate currently rejects every mobility provider whose key is not `mock-mobility`. This is safe for WP03-WP05, but it means simply switching to Valhalla/GraphHopper later will make every plan fail.

Do not fix that by letting the feasibility gate call the network. Instead:

```text
real provider call
-> freeze TravelEstimate facts
-> MobilitySnapshot
-> deterministic feasibility gate
```

The prepared patch includes that boundary.
