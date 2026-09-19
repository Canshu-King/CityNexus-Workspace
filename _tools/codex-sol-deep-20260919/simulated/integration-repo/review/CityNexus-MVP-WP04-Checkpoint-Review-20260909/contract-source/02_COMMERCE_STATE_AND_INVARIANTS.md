# WP04 Commerce State and Invariants

## Preconditions

Commerce writes require:

- Journey exists;
- Journey status is `PLANNED` for the canonical WP04 flow;
- `active_plan_version_id` references the currently selected plan;
- selected PlanVersion status is `SELECTED`;
- requested Activity belongs to that selected plan and that Journey;
- Activity is not terminal (`COMPLETED/SKIPPED/CANCELLED`);
- selected plan still passes the authoritative deterministic feasibility layer after the pre-WP04 repair.

Do not book arbitrary Activities from stale CANDIDATE plans.

## Booking lifecycle

```text
DRAFT -> PENDING -> CONFIRMED -> COMPLETED
             |          |
             v          v
           FAILED     CANCELLED
```

Mock create may collapse the transient DRAFT/PENDING persistence and persist the authoritative final result (`CONFIRMED` or `FAILED`) if the provider call is synchronous, provided provider-call evidence records the outcome.

## Order lifecycle

```text
DRAFT -> PENDING -> CONFIRMED -> FULFILLED
             |          |
             v          v
           FAILED     CANCELLED
```

For MVP, create a deterministic CONFIRMED order for a valid tradable service; payment remains separate.

## PaymentTransaction lifecycle

```text
INITIATED -> AUTHORIZED -> SUCCEEDED
    |            |            |
    v            v            +-> REFUNDED
  FAILED       VOIDED
```

MVP rules:

- `AUTHORIZE` successful mock outcome -> `AUTHORIZED`.
- `CAPTURE` successful mock outcome -> `SUCCEEDED`.
- provider failure -> `FAILED`.
- `REFUND` only from `SUCCEEDED` and -> `REFUNDED`.
- `VOID` only from `AUTHORIZED` and -> `VOIDED`.

Do not infer success from local intent. Provider-normalised outcome is authoritative (BR-018).

## Commitment lifecycle

```text
PROPOSED -> ACTIVE -> FULFILLED
    |          |
    |          +-> CANCELLED
    |          +-> BREACHED
    +-> CANCELLED
```

Commitment strength is separate from lifecycle and separate from payment status.

### Non-negotiable strength rule

The source domain has five strength levels C0..C4; current four-value package mapping is lossy. Before WP04 persistence, reconcile the exact five enum values from the frozen YAML. `PAID` must not be used as a strength enum merely because a payment succeeded.

### MVP deterministic rank policy

Use rank 0..4 internally for policy reasoning; map rank to the exact source strength code after reconciliation.

Suggested engineering policy (not a claim about source labels):

- rank 0: no meaningful external/user commitment;
- rank 1: low-impact soft commitment;
- rank 2: provider-confirmed reservation / material commitment;
- rank 3: paid/high-change-cost commitment;
- rank 4: anchored fixed-time commitment that normal replanning must preserve.

Payment success alone can raise strength, but **must not alone force rank 4**. Canonical River Cruise reaches rank 4 because it is provider-confirmed + paid + fixed-time/user-locked/high impact.

## Canonical stable identity for later replanning

Do not rely only on a PlanVersion-specific Activity UUID. Store enough commitment policy evidence to rebuild a stable semantic lock:

```json
{
  "semantic_key": "place-river-cruise",
  "scheduled_start_at": "2026-10-10T15:30:00+08:00",
  "scheduled_end_at": "2026-10-10T16:30:00+08:00",
  "fixed_schedule": true,
  "strength_rank": 4,
  "source_refs": {
    "booking_id": "...",
    "payment_transaction_id": "..."
  }
}
```

This may live in `policy_json` for the MVP to avoid unnecessary schema growth. It must be deterministic and sufficient for WP06 lock preservation.

## Cancellation policy

- confirmed unpaid cancellable booking may be cancelled by provider;
- cancellation outcome must be provider-authoritative;
- successful cancellation cancels the booking and associated non-paid commitment;
- paid/anchored canonical booking should reject direct cancellation until refund/exception policy is implemented, rather than silently destroy a high-strength commitment.
