# Cross-layer mismatches

## CX-SOL-001 — P1 — verified real defect

Proof: `/experience` emits `active_plan.current_activity_id`. Before the candidate patch, `V8Experience.Live` read `activities[0]`, `activities[1]`, `legs[0]`; `LiveSecondary` repeated the same assumption. With activities `act-1, act-2, act-3` and cursor `act-2`, the UI showed completed `act-1` as Now.

- Minimal repro: `python tests/repro_live_current_activity.py`
- Candidate patch: `candidate_patches/CX-SOL-001-live-current-activity.patch`
- Regression: `candidate_patches/codex-live-current-activity.spec.ts`
- Verification: typecheck PASS, production build PASS, Playwright regression 1/1 PASS.
- Existing Qoder coverage: not covered; its Live fixture always points to the first activity.
- Owner action: apply after review and retain a fixture where the cursor is not index zero.

## CX-SOL-002 — P2 — verified integration risk, not patched

Accepted recovery is represented across two resources: proposal=`ACCEPTED`, trigger Event often=`ACKNOWLEDGED`. Frontend correctness depends on fetching `/replans`, collecting accepted `trigger_event_id` values and joining them to disruptions. The current shared helper is correct; consumers that inspect Event status alone will reopen a handled decision.

- Minimal repro: `python tests/repro_ack_linkage.py`
- Existing Qoder coverage: yes, ACK/resolution rendered tests.
- Owner action: preserve the helper during merges; consider an API-derived `handled_by_proposal_id` or resolution projection in a versioned contract.

## CX-SOL-003 — P2 — verified observability gap, not patched

Backend hard eligibility depends on `fact_quality`, but the V8 frontend leg type does not carry it. This is safe while hard decisions remain server-owned, but unsafe if future UI code equates provider/provenance strings with verified hard truth.

- Existing Qoder coverage: backend allowlist is covered; frontend negative inference is not.
- Owner action: either expose a normalized quality/eligibility field or document that UI labels are descriptive only.

## Ruled-out candidate: budget overclaim

The Studio computes activity-only coverage, but current copy explicitly disclaims whole-trip verification. This is not a defect at the inspected snapshot.

