# Track L — Cross-projection differential oracle

Goal:
Automatically catch contradictions like CX-SOL-001.

Build a normalized semantic snapshot from the authoritative backend state:
- journey_id
- active_plan_id
- current_activity_id
- current activity semantic identity
- next activity semantic identity
- next leg identity
- open/handled disruptions
- accepted proposal linkage
- protected commitments
- budget evidence level
- mobility trust/eligibility

Compare that oracle against every available consumer projection:
- journey/plan API
- V8 data payload
- Today
- Live
- Trips
- Map/current-position projection
- any execution/V10 projection still reachable

This must be data-driven and run across generated fixtures:
- 1 activity
- 2 activities
- 3+ activities
- cursor first/middle/final
- cursor missing
- cursor stale
- open disruption
- ACK-only
- accepted linked proposal
- unrelated accepted proposal
- budget none/partial/full
- provider live/mock/unavailable

Produce:
- projection_oracle.py
- PROJECTION_DIVERGENCE_REPORT.md
- replay JSON for divergences
- focused regression tests

A projection mismatch is a candidate product defect even when each individual
component's local tests pass.
