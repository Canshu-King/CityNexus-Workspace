# Payment Idempotency and Failure Semantics

## Scope

Applies to `POST /journeys/{journey_id}/transactions`.

## Canonical semantic request

Fingerprint only side-effect-relevant fields:

```text
journey_id
provider_key
booking_id or order_id
transaction_type
amount_minor
currency
```

Do not include timestamps, trace IDs or volatile fields.

## New key flow

```text
check idempotency storage key absent
  -> validate target/amount/state
  -> call provider once
  -> persist provider_call
  -> persist PaymentTransaction
  -> if successful capture: strengthen Commitment
  -> persist idempotency response
  -> audit
  -> commit
```

## Replay flow

Same scoped key + same canonical request:

```text
return stored logical response
no provider call
no new PaymentTransaction
no duplicate commitment strengthening
```

## Conflict flow

Same scoped key + different canonical request:

```text
409 IDEMPOTENCY_CONFLICT
no provider call
no database mutation except optional rejected audit
```

## Provider failure

```text
PaymentTransaction.status = FAILED
provider external/ref or failure code retained if safe
Commitment strength unchanged
no false PAID/Anchored result
```

A failed result itself should be idempotently replayable.

## Atomicity caveat

A real external provider cannot participate in the SQLite transaction. WP04 uses deterministic local adapters, but preserve production-compatible ordering: resolve idempotency before external call, store authoritative provider outcome, and never fabricate provider success after an exception.
