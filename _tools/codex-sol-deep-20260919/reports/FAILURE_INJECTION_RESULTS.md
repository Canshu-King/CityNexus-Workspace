# Failure-injection results

Focused executable run: 81 tests passed in 18.75 seconds across mobility truth, physical identity, live hard fallback, replan endpoints, acceptance/idempotency, material diffs, weather degradation and provider adapters.

Model run: 5,000 randomized sequences × 80 steps = 400,000 transitions; all 12 required invariants passed. Seed: `20260919`. Result: `artifacts/stateful_audit_result.json`.

Verified behavior:

- Valhalla timeout and malformed route payload produce controlled provider errors and no invented ETA.
- Live-provider failure does not promote synthetic mock facts to hard truth.
- Hard mobility accepts only the explicit allowlist.
- Duplicate/ambiguous physical identity fails closed.
- ACK remains open; only a linked accepted proposal closes its consumer decision.
- Replan accept is base-plan, trigger, feasibility and idempotency gated.
- Protected C4 commitments are remapped or acceptance fails.
- Weather/AI provider failures produce explicit degradation, not fabricated facts.

Static-only limitation: a real external map-tile outage was not induced because no infrastructure deployment/network target was authorized. Map degradation was inspected at component/error-boundary level. Booking-import behavior relied on existing focused gates and source inspection rather than mutating an external provider.

One real product defect was found outside provider failure handling: CX-SOL-001. Its isolated candidate patch and browser regression are included and pass.

