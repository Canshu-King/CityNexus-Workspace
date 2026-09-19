# Post-Gate Hardening Findings

This file translates the independent adversarial failures into executable invariants.

## Replan/Event ownership and terminality

A disruption Event is actionable only while:

```text
Event.status in {DETECTED, ACKNOWLEDGED}
AND
no ACCEPTED ReplanProposal already handles that Event
```

After a proposal is accepted:

```text
Event DETECTED -> ACKNOWLEDGED
accepted proposal -> ACCEPTED
accepted candidate PlanVersion -> ACTIVE
base PlanVersion -> SUPERSEDED
sibling PRESENTED proposals -> INVALIDATED
sibling CANDIDATE PlanVersions -> REJECTED
```

This prevents an old disruption from minting endless replacement universes.

## Replan rejection

Rejecting a proposal must retire both artifacts:

```text
ReplanProposal PRESENTED -> REJECTED
PlanVersion CANDIDATE -> REJECTED
```

Re-reject is safe/idempotent and must not duplicate the rejection audit.

## Replan accept idempotency

Formal contract already requires `Idempotency-Key`; runtime should honor it.

Required behavior:

```text
same key + same proposal -> replay original 200 response
same key + different proposal -> 409
missing/invalid key -> 422
```

This is application idempotency, not file/hash verification work.

## JourneyTwin degradation projection

Do not use only the latest Event. Aggregate `degraded_providers` from all unresolved Events:

```text
status in {DETECTED, ACKNOWLEDGED}
```

If any degraded provider remains:

```text
JourneyTwin.projection_status = DEGRADED
```

When all relevant provider Events are resolved/ignored, the projection can return to READY.

## Replan metadata

Any content or timing change must recompute at least:

```text
total_cost_minor
estimated_duration_min
ReplanDiff
FeasibilityEnvelope
```

`utility_score` and `score_breakdown` still need a separate P1 scoring repair before they are exposed as trustworthy comparison evidence.

## ReplanDiff protection evidence

Diff semantic identity should use:

```text
place_id
OR city_service_id
OR activity.id fallback
```

Protection evidence should use:

```text
Activity.locked
OR matching durable ACTIVE C4 semantic/time anchor
```

The `Activity.locked` flag is not the source of truth for a real commerce-backed commitment.
