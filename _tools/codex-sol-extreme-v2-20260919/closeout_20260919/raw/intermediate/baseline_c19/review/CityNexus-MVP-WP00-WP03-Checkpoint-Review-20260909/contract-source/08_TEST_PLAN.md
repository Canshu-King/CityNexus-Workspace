# 08 - Test Plan

Machine-readable checklist: `tests/test_matrix.csv`.

## Test layers

### Unit
Pure domain/state/replanning rules. No network and preferably no database.

### Integration
FastAPI service + SQLite + repositories + mock provider adapters.

### Contract
OpenAPI response/request compatibility, mock-provider interface contracts and error envelope.

### E2E
Browser/API vertical-slice scenarios across the whole MVP.

### Security/robustness
Input validation, ID ownership, idempotency, stale replan acceptance, provider failure and AI outage.

## Release gates for the first demo

A demo build is green only when all of these are true:

1. Backend unit/integration tests pass.
2. Frontend build passes with no TypeScript errors.
3. OpenAPI YAML parses and the implemented endpoints match the MVP subset.
4. SQLite schema can be created from empty state.
5. Demo seed is deterministic and repeatable.
6. Canonical journey can be created and planned.
7. Booking/payment simulation creates a commitment.
8. Journey can start and JourneyTwin can be read.
9. Closure event generates a feasible replan.
10. Locked River Cruise remains unchanged.
11. Proposal acceptance atomically changes the active plan.
12. Repeating the same acceptance with the same idempotency key is safe.
13. A stale proposal is rejected.
14. AI-disabled mode still completes the core flow.
15. Audit/history shows the important state changes.

## Test data rules

- Do not use random provider outcomes in tests.
- Freeze canonical fixture timestamps.
- Use deterministic UUIDs in seed fixtures when useful.
- Tests must not require public internet access.
- Every bug in journey/replanning state should receive a regression test before being marked fixed.

## Engineering performance targets

These are internal MVP targets, not source-derived NFR thresholds:

- local non-AI GET/CRUD API p95 target: < 500 ms;
- deterministic plan/replan generation target on mock catalog: < 2 s for the canonical scenario;
- frontend primary interaction should not block on AI response for core feasibility.

If the frozen NFR baseline contains stricter/exact thresholds, the frozen baseline wins and this section must be updated.
