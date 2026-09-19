# Cross-layer contract map

Evidence snapshot: integration commit `1de4e0c569349d7eee4bc22995cc49c487e3279e`. Facts below are source-verified unless marked inference.

## Journey, plan and visible execution

`Journey.active_plan_version_id` and `Journey.current_activity_id` are backend truth. `stay_mobility._active_plan_payload` emits both as `active_plan.id` and `active_plan.current_activity_id`, with activities and legs sorted by `sequence_no`. Today, Live and Trips all consume `/api/v1/journeys/{id}/experience`.

The backend correctly advances and remaps the cursor. The frontend Map page already uses `nextActivityOf`, which searches `current_activity_id`. Before the candidate patch, `Live` and `LiveSecondary` bypassed that contract and selected array indexes 0/1. This is CX-SOL-001.

## Disruption, ACK, resolution and proposal linkage

The Event lifecycle is `DETECTED -> ACKNOWLEDGED -> RESOLVED` (with `IGNORED` as another closed state). `acknowledge_journey_recovery` explicitly records `resolved: false`; ACK never clears review truth.

Replan generation requires a trigger Event on the same journey in DETECTED or ACKNOWLEDGED state. Acceptance requires a PRESENTED proposal, matching active base plan, actionable trigger, persisted mobility evidence and a fresh feasibility pass. It activates the proposed plan, remaps the execution cursor and active C4 commitments, invalidates competing candidates, and persists the idempotent response.

Acceptance changes a DETECTED trigger to ACKNOWLEDGED, not RESOLVED. The consumer closes only the linked trigger by joining ACCEPTED proposals through `trigger_event_id` in `disruptionState.isDisruptionOpen`. This is deliberate and tested, but it is a cross-resource semantic dependency (CX-SOL-002).

## Mobility provenance

Hard mobility is server-owned. `MobilitySnapshot.hard_minutes` accepts only `LIVE_PROVIDER_CAPTURE` and `EXPLICIT_FROZEN_FIXTURE`; unknown, synthetic-default and untagged facts fail closed. Runtime live failure cannot launder deterministic mock data into hard evidence.

The V8 leg projection exposes provider, provenance, snapshot id and freshness fields at runtime. Its TypeScript shape includes provider/provenance but not normalized `fact_quality`; therefore frontend code must not infer hard eligibility from a provider label (CX-SOL-003).

## Bookings and protected commitments

Active `C4_Anchored` commitments are included in generation and acceptance feasibility. Acceptance remaps plan-local `activity_id` using durable semantic/time anchors. If remapping cannot preserve the execution position or commitment, acceptance returns 409 before mutation.

## Budget evidence

`budgetEvidenceCoverage` distinguishes NONE/PARTIAL/FULL and requires explicit known statuses for FULL. The Studio currently evaluates activity costs only. Its English and Chinese copy explicitly says whole-trip budget, including stay and transport, is not verified. No whole-trip overclaim was found.

## Consumer consistency

After CX-SOL-001 is applied, Today/Live/Trips derive plan identity from the same `active_plan`; Live derives now/next from the same `current_activity_id`; accepted triggers are handled through the same disruption helper. The model harness exercised 400,000 transitions across the twelve required invariants without a model failure.

