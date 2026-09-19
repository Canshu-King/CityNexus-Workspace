# Replan Lifecycle and Idempotency Contract

## Proposal state machine

```text
candidate generated
      |
      v
PRESENTED
  |        \
accept     reject
  |          \
  v           v
ACCEPTED    REJECTED

Sibling proposals from the superseded base become INVALIDATED.
```

`GENERATED` remains a conceptual/internal state if asynchronous generation is added later. For the current synchronous API, a returned proposal should already be PRESENTED.

## Accept-time checks

Before activation:

1. proposal is PRESENTED;
2. Journey is ACTIVE;
3. proposal base is the current ACTIVE plan;
4. trigger Event belongs to this Journey;
5. proposed plan still passes authoritative deterministic feasibility;
6. active C4 commitments are preserved by semantic identity + scheduled anchor;
7. current execution position can be mapped onto the proposed plan.

Only after those checks may the transaction supersede the base.

## Idempotency scope

Use a namespaced operation key, e.g.:

```text
replan.accept:{Idempotency-Key}
```

Fingerprint only semantic request content (`proposal_id`). Store the successful response for exact safe replay. The existing idempotency table can be reused.

Do not use this feature to reintroduce package/file hashing. It is business request idempotency only.

## Event status

For now:

```text
DETECTED -> ACKNOWLEDGED on accepted recovery
```

Do not automatically mark RESOLVED merely because a plan was changed. A weather outage/closure/provider incident can continue to exist after the Journey has recovered. RESOLVED should mean the underlying Event itself is no longer active.
