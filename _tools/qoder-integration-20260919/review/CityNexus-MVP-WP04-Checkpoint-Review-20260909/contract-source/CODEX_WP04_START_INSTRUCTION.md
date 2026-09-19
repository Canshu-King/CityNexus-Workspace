# CODEX — WP04 exact start instruction

## Read this first

You are currently finishing the small pre-WP04 WP03 repair. **Do not start WP04 until that repair's stop gate is green.**

User rule: **do not calculate/check/report file or package hashes**. Do not spend quota on hash manifests or SHA verification. Functional idempotency request fingerprinting is application logic, not package-integrity work; use the supplied canonical-request semantics.

Once the WP03 repair is green, do not redesign CityNexus. Use this assist package as the WP04 implementation contract.

## Step 0 — one mandatory read-only source check

Read the local frozen v0.4.2 domain YAML only for `commitment_strength` **and `commitment_source_type`**. Record the exact values/order. Use `tools/extract_wp04_domain_enums.py` if its YAML shape matches; it must fail rather than guess.

Reason: current package's four-level `FLEXIBLE/RESERVED/PAID/LOCKED` mapping is lossy, while FR-030 requires exactly five source levels `C0...C4`, and BR-011 says payment alone does not define strength.

Do not guess C1-C3 or source-type values. Do not re-read unrelated domain material.

## Step 1 — WP04A only

First run the low-conflict scaffold helper if the current repo still matches the checkpoint:

```powershell
python <assist>\tools\apply_wp04_scaffold.py D:\moodle\CityNexus D:\moodle\CityNexus\domain-model\<current-v0.4.2-yaml>
```

This helper was tested on a fresh copy of the current checkpoint and preserved the existing suite while adding pure WP04 reference tests. Inspect its diff; do not blindly overwrite concurrent WP03 fixes.

Then implement/confirm:
- lossless five-level commitment representation;
- ORM: Commitment, Booking, Order, PaymentTransaction (`transactions` table), ProviderCall, IdempotencyKey;
- preserve existing SQL tables rather than creating duplicates.

Run old tests + new schema/enum tests. If red, stop and fix. No endpoint work until green.

## Step 2 — integrate supplied provider/policy reference modules

Use, adapt or copy:

```text
reference_patch/backend/app/commerce/commitment_policy.py
reference_patch/backend/app/commerce/idempotency.py
reference_patch/backend/app/integrations/commerce_ports.py
reference_patch/backend/app/integrations/mock/commerce_providers.py
```

Keep adapters deterministic and network-free.

## Step 3 — Booking

Implement only booking/commitment slice first:

```text
PLANNED Journey
+ SELECTED Plan
+ Activity belongs to selected plan
-> MockBookingProvider
-> Booking CONFIRMED/FAILED
-> ACTIVE Commitment only on confirmed source event
```

Do not allow booking an Activity from an unselected CANDIDATE/stale plan.

Run CNX-I-011 plus new ownership/failure tests. Stop locally if they fail.

## Step 4 — Order

Implement small deterministic order path using `wp04_commerce_catalog.json`. Request should rely on SKU + quantity; server computes authoritative unit prices and total. Do not let client forge total/provider result.

## Step 5 — Payment/idempotency

Implement target XOR validation, amount/currency validation, idempotency before provider call, provider-authoritative PaymentTransaction, commitment strengthening in same DB transaction, forced failure behavior. Prove CAPTURE for both a Booking target and an Order target. Do not invent ambiguous REFUND/VOID semantics in this cycle unless an original transaction reference is modelled.

Same key/same request -> same logical transaction, zero duplicate provider call.
Same key/different request -> 409 before provider call.

Run CNX-I-012/013 and reference semantics tests.

## Step 6 — canonical River Cruise witness

Create booking/payment against selected 15:30 River Cruise.

Required final evidence:

```text
Booking.status = CONFIRMED
PaymentTransaction.status = SUCCEEDED
Commitment.status = ACTIVE
Commitment strength rank = 4 / exact source C4 code
semantic_key = place-river-cruise
scheduled_start_at = 2026-10-10T15:30:00+08:00
```

The strength decision must use fixed/user-lock/provider/payment facts. Do not implement `if payment_succeeded: C4`.

## Step 7 — full WP04 gate

Must pass:
- all existing tests;
- CNX-I-011/012/013;
- CNX-C-006/007;
- forced booking failure => no false confirmed commitment;
- forced payment failure => no paid/anchored upgrade;
- idempotency replay/conflict tests;
- stale/unselected Activity booking tests;
- persistence across new DB session/restart smoke;
- no secret/card fields persisted/logged;
- canonical anchored River Cruise evidence.

Update requirement statuses conservatively, only with actual acceptance/test evidence.

Then STOP and produce one repo-relative checkpoint for GPT review. Do not begin WP05 in the same Codex run.

## Do not do in WP04

- frontend;
- real payment/booking network APIs;
- AI;
- JourneyTwin;
- events/replanning implementation;
- Visio;
- Alembic polishing unrelated to a concrete schema failure;
- performance refactors;
- file/package hash checks.
