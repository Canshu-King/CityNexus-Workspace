# WP04 gate report

All commands below were run from `D:\moodle\CityNexus`. The WP04 contract's
offline/mock-only boundary was retained.

## Automated gates

```text
$env:PYTHONPATH='backend'; .venv\Scripts\python.exe -m pytest -q backend\tests
87 passed, 2 warnings in 23.59s

$env:PYTHONPATH='backend'; .venv\Scripts\python.exe -m pytest -q _incoming_wp04_preflight_assist_20260909\CityNexus_WP04_Preflight_Assist_20260909\tools
5 passed in 0.03s

.venv\Scripts\ruff.exe check backend
All checks passed!

.venv\Scripts\ruff.exe format --check backend
38 files already formatted

.venv\Scripts\python.exe ...\tools\wp04_preflight.py .
WP04 PRE-FLIGHT
PASS commitment SQL exposes five levels: ['C0_Flexible', 'C1_Preferred', 'C2_Reserved', 'C3_Guaranteed', 'C4_Anchored']
SUMMARY p0=0 p1=0
```

The supplied enum extractor was also run against the local frozen v0.4.2 YAML;
its exact output is copied to `source-reconciliation.md`.

## WP04A-0 evidence

- `backend/tests/test_wp04a0_bridge.py` proves two visits to the same Place can
  be locked independently by relative start, while an unmatched start fails.
- The same test proves an activity currency mismatch is rejected without a
  HARD `BUDGET_MAX`, and a planned Journey budget-currency mutation is rejected
  atomically while its selected plan remains unchanged.
- The same test proves selecting the current selected plan twice leaves one
  `plan.selected` audit row. The route is now a no-op for any already-current
  SELECTED plan.

## WP04A-G acceptance evidence

- Source enum and ORM/schema gate: exact five levels in SQL, OpenAPI and
  Pydantic validation; invalid sixth values are rejected.
- Provider ports and mocks: booking availability/create/cancel/status and
  payment authorize/capture/refund/void/status are deterministic and local.
- Booking: selected-plan/activity ownership, planned-Journey precondition,
  stale/cross-Journey rejection before a provider call, persisted confirmed or
  failed provider outcome, and unpaid cancellation.
- Order: SKU + quantity input, server catalog pricing, forged client price
  ignored, persisted order commitment, and Order-target capture.
- Payment: booking/order target XOR, ownership and authoritative amount/currency
  checks, provider-authoritative success/failure, receipt `external_ref`, and
  idempotency replay/conflict before provider calls.
- Commitment policy: payment alone does not imply C4; the flexible paid-order
  regression remains below C4. The River Cruise reaches exact source C4 only
  after confirmed booking, capture, fixed schedule/user anchor and low
  replaceability are all present. `Activity.locked` is treated as an input
  factor, never as proof of payment or pre-existing C4.
- Safety: sensitive payment fields are rejected at the request boundary and no
  such values are persisted or logged; only mock provider references are used.
- Persistence: a second process/session retrieved the confirmed booking,
  succeeded transaction, active `C4_Anchored` commitment, and provider
  external reference unchanged.

## Representative fresh-process smoke output

```text
{'booking_status': 'CONFIRMED', 'transaction_status': 'SUCCEEDED',
 'commitment_level': 'C4_Anchored',
 'external_ref': 'mock-payment:<provider-reference>:succeeded'}
```

## Contract/route smoke

The OpenAPI document parsed as 3.1.0 with 33 paths. All seven WP04 routes are
registered, and the Commitment enum is exactly the frozen five-value tuple.

No frontend, Visio, event/replanning, AI, live provider, real gateway, or WP05
work was started. No SHA, file, or archive-integrity checks were run.
