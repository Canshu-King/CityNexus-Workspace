# CityNexus WP04 Preflight Assist — Booking / Payment / Commitment

Prepared while Codex finishes the small pre-WP04 WP03 correctness repair.

This package is **not** permission to start WP04 before the WP03 stop gate is green. It is a quota-saving engineering kit so Codex can integrate tested pieces rather than redesigning commerce architecture from scratch.

## User rule: no package/file hash work

Do not spend time or quota on SHA/file/package hash verification or hash manifests. The existing database column `idempotency_keys.request_hash` is merely a legacy application field name. The reference idempotency code stores canonical request JSON and does not require cryptographic hashing.

## Start here

For Codex, read in this order only:

1. `CODEX_WP04_START_INSTRUCTION.md`
2. `00_PREFLIGHT_FINDINGS.md`
3. `10_WP04_WORK_PACKAGE.md`
4. `11_INTEGRATION_PATCH_MAP.md`

Then use the supplied code/tests directly. Do not reread the full project history.

## What is already prepared

- WP04 architecture and DB/provider transaction boundaries.
- Booking/Order/Payment/Commitment state invariants.
- Complete requirements-focused contract delta for IR-006/IR-007.
- Schema/ORM delta for the six already-existing commerce tables.
- Deterministic mock BookingProvider and PaymentProvider ports/adapters.
- Pure multi-factor commitment-strength policy.
- Stable semantic lock identity/time policy for later WP06 replanning.
- Idempotency replay/conflict semantics.
- Security validators for target ownership, amount/currency and sensitive card fields.
- Server-authoritative order pricing reference + deterministic WP04 commerce catalog.
- 40-row WP04 acceptance/test matrix and requirement traceability.
- WP04A–WP04G micro work packages.
- A read-only exact source enum extractor that refuses to guess.
- A low-conflict `apply_wp04_scaffold.py` helper for WP04A/B.
- Framework-free reference service plus SQLAlchemy orchestration template.
- Golden-scenario endpoint acceptance-test template.
- Preflight checker and validation reports.

## Critical source-contract finding before WP04

The current SQL/OpenAPI blueprint exposes only four commitment `level` values:

`FLEXIBLE / RESERVED / PAID / LOCKED`

The reconciled frozen source requires **five** commitment-strength levels `C0..C4`, with known endpoints `C0_Flexible` and `C4_Anchored`; FR-030 requires exactly five. BR-011 also requires multi-factor strength derivation, so payment status cannot double as strength.

Codex must perform one tiny read-only lookup of the local frozen v0.4.2 YAML for:

- exact `commitment_strength` values/order;
- exact `commitment_source_type` values.

Do not guess the missing names. `tools/extract_wp04_domain_enums.py` exists specifically to make this a mechanical read rather than another model-reasoning task.

## Another contract correction already solved here

The blueprint OrderCreate allowed a client to submit `unit_amount_minor`. WP04 should treat price as server/provider-authoritative. The supplied `wp04_commerce_catalog.json` + `order_pricing.py` uses `{sku, quantity}` and computes the total server-side.

## Scope discipline

WP04 remains offline/local. Do not add real booking/payment network APIs, card fields, provider credentials, frontend, AI, JourneyTwin, event/replanning code, Visio work, unrelated Alembic polishing, or performance refactors.
