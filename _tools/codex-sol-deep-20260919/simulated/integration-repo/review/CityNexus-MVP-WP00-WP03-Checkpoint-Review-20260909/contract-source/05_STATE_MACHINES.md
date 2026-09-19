# 05 - State Machines

The handoff confirms that Journey, Commitment and ReplanProposal have state-machine concepts, but it does not preserve the exact enum values. The lifecycles below are **implementation contracts for the MVP** and must be reconciled with the current local domain YAML before code generation if exact states are already defined there.

## Journey

```text
DRAFT
  | select feasible plan
  v
PLANNED
  | start journey
  v
ACTIVE
  | all required activities terminal
  v
COMPLETED

DRAFT/PLANNED/ACTIVE -> CANCELLED  [explicit user/system cancellation policy]
```

Guards:
- DRAFT -> PLANNED requires a selected feasible PlanVersion.
- PLANNED -> ACTIVE requires an active/selected plan and valid journey time context.
- ACTIVE -> COMPLETED requires no required future activity remaining.

## PlanVersion

```text
CANDIDATE -> SELECTED -> ACTIVE -> SUPERSEDED
     \          \          \
      -> REJECTED  -> REJECTED  -> (terminal)
```

Rules:
- Multiple CANDIDATE versions may coexist.
- A journey has at most one ACTIVE plan.
- Accepting a ReplanProposal creates/activates the proposed plan and marks the old ACTIVE plan SUPERSEDED atomically.

## Activity

```text
PLANNED -> READY -> ACTIVE -> COMPLETED
   |         |        |
   +-------> SKIPPED  +----> CANCELLED
```

Locked activities cannot be cancelled by the replanner unless a deterministic exception policy explicitly makes preservation impossible and the proposal is not auto-activatable.

## Commitment

Lifecycle state and commitment strength are separate.

Lifecycle:

```text
PROPOSED -> ACTIVE -> FULFILLED
    |          |
    |          +-> CANCELLED
    |          +-> BREACHED
    +-> CANCELLED
```

Strength (`level`):

```text
FLEXIBLE < RESERVED < PAID < LOCKED
```

MVP policy:
- LOCKED is a hard preservation gate.
- PAID and RESERVED strongly prefer preservation and affect the commitment-preservation score; if a provider policy makes cancellation/rebooking lossless, deterministic rules may permit change.

## Booking

```text
DRAFT -> PENDING -> CONFIRMED -> COMPLETED
             |          |
             v          v
           FAILED     CANCELLED
```

## Order

```text
DRAFT -> PENDING -> CONFIRMED -> FULFILLED
             |          |
             v          v
           FAILED     CANCELLED
```

## Transaction

```text
INITIATED -> AUTHORIZED -> SUCCEEDED
    |            |            |
    v            v            +-> REFUNDED
  FAILED       VOIDED
```

For the mock provider, payment behavior is deterministic from the request fixture; do not use randomness in contract tests.

## Event

```text
DETECTED -> ACKNOWLEDGED -> RESOLVED
    |             |
    +-----------> IGNORED
```

An event may trigger zero or more ReplanProposals. Not every event requires replanning.

## ReplanProposal

```text
GENERATED -> PRESENTED -> ACCEPTED
                    |-> REJECTED
                    |-> EXPIRED
                    |-> INVALIDATED
```

Hard guards for acceptance:
- hard_constraints_passed == true
- locked_commitments_preserved == true
- journey.active_plan_version_id == base_plan_version_id
- proposed plan still exists and is feasible under the latest deterministic snapshot
- idempotency key has not been used for a different request

## JourneyTwin

JourneyTwin is a projection, not a source-of-truth aggregate.

Projection health:

```text
READY -> STALE -> READY
  |        |
  +------> DEGRADED -> READY
```

The projection is rebuilt/refreshed from source-of-truth records after significant state changes.
