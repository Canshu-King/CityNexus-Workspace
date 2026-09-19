# WP04 Micro Work Packages

Do these only after the pre-WP04 WP03 repair is green.

## WP04A — Source enum reconciliation + commerce ORM

Tasks:
- read exact five source commitment strengths **and exact `commitment_source_type` enum** from frozen YAML;
- fix four-level lossy schema/API mapping;
- add ORM models for Commitment, Booking, Order, PaymentTransaction, ProviderCall, IdempotencyKey;
- no endpoints yet.

Gate:
- exact five strength values accepted, invalid sixth rejected;
- ORM metadata matches SQL;
- all prior tests green.

## WP04B — Provider ports + deterministic mock adapters

Tasks:
- BookingProvider availability/create/cancel/status;
- PaymentProvider authorize/capture/refund/void/status;
- fixture-backed success/failure;
- provider_call recorder.

Gate:
- CNX-C-006/007 pass;
- deterministic repeated inputs produce repeated normalized outcomes;
- no network/runtime secret.

## WP04C — Booking + commitment creation

Tasks:
- validate PLANNED/SELECTED ownership;
- booking slots/status endpoints if adopting contract delta;
- create booking;
- provider-authoritative CONFIRMED/FAILED result;
- create/strengthen ACTIVE commitment via pure policy;
- cancellation for a cancellable unpaid fixture.

Gate:
- CNX-I-011 pass;
- stale/candidate-plan Activity rejected;
- forced booking failure creates no false confirmed commitment.

## WP04D — Order

Tasks:
- validate `{sku, quantity}` items;
- compute SKU prices/total server-side from the supplied deterministic catalog;
- derive fulfilment window from linked Activity for MVP;
- create CONFIRMED deterministic order and commitment evidence.

Gate:
- invalid/empty item input rejected;
- total cannot be client-forged;
- record persists across new DB session.

## WP04E — Payment + idempotency

Tasks:
- transaction target XOR validation;
- amount/currency validation;
- idempotency resolution;
- provider call;
- PaymentTransaction persistence;
- successful CAPTURE strengthens the same semantic commitment;
- support both Booking and Order targets for CAPTURE;
- forced failure does not strengthen;
- receipt external_ref retained.

Gate:
- CNX-I-012/013 pass;
- same key/same request no duplicate provider call/transaction;
- same key/different request 409;
- failed transaction replay is safe.

## WP04F — Canonical Anchored/LOCKED witness

Tasks:
- use River Cruise Activity from selected plan;
- booking CONFIRMED;
- capture SUCCEEDED;
- derive source C4 strength using multiple facts;
- persist stable semantic lock identity/time in policy_json.

Gate:
- ACTIVE commitment exists at source rank 4;
- `semantic_key=place-river-cruise` and start 15:30 are preserved;
- payment alone negative test does not reach rank 4.

## WP04G — Traceability/checkpoint

Tasks:
- audit booking/payment high-risk outcomes;
- update requirement status only where acceptance evidence exists;
- run entire old+new test suite;
- restart/persistence smoke test;
- package repo-relative checkpoint.

Stop after checkpoint. Do not start WP05 in the same turn.
