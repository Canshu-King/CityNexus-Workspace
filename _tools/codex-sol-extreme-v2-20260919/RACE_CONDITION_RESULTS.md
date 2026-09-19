# Race condition results

## Baseline, real API + SQLite

`tests/concurrency_harness.py` drives actual FastAPI endpoints in synchronized threads and inspects persisted rows afterward.

Three verified defects reproduced:

1. Same proposal + same idempotency key: one 200 and one SQLAlchemy `IntegrityError` on `idempotency_keys.key`.
2. Two proposals on one base plan: both 200; two ACCEPTED proposals and two ACTIVE plans persisted.
3. Booking CAPTURE vs replan ACCEPT: both succeeded, but an ACTIVE C4 commitment pointed to an activity on the superseded plan.

The same-proposal/different-key path and restart/retry path remained coherent.

Raw baseline: `replay_cases/concurrency_harness.json`.

## Candidate

The isolated candidate serializes authoritative writes per Journey, holds the payment guard through commit, expires stale session state after lock acquisition, and remaps a captured booking commitment to the equivalent activity on the current ACTIVE plan. If remapping cannot be proved, capture fails closed.

Five independent reruns of all five schedules produced zero defects (`concurrency_after_fix_1.json` through `_5.json`). The candidate is intentionally labelled process-local: production multi-worker deployment still requires database/advisory locking.
