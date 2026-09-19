# Track K — Concurrency / race-condition audit

Goal:
Attack the recovery lifecycle under concurrent clients and retries.

Use isolated backend + isolated DB. Prefer real HTTP/ASGI calls.

Scenarios:
1. ACK and ACCEPT race on the same disruption.
2. Two concurrent accepts of the same proposal.
3. Two different proposals for the same trigger accepted concurrently.
4. Accept stale proposal while a newer replan is being generated.
5. Duplicate POST retries with and without idempotency support.
6. Booking confirmation/import races with replan acceptance.
7. Read Today/Live/Trips during accept transaction.
8. Provider result arrives after proposal has become stale.
9. Two disruptions overlap and one proposal is accepted.
10. App/server restart between proposal creation and acceptance, then retry.

Assert:
- no duplicate activities/commitments
- one coherent active plan
- no unrelated disruption resolution
- no stale proposal becomes authoritative
- no protected booking silently disappears
- retry result is deterministic / explicitly rejected
- persisted state survives restart coherently
- UI/API projection eventually converges

Deliver:
- concurrency_harness.py
- RACE_CONDITION_RESULTS.md
- minimized race schedules for defects
- candidate patches only for verified defects
