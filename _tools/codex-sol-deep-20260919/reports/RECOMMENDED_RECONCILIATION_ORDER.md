# Recommended reconciliation order

1. Freeze and record source SHAs; do not merge against a moving integration branch.
2. Establish backend truth v6 first: mobility fact quality, physical identity, proposal linkage, C4 preservation and idempotency.
3. Preserve shared frontend truth helpers (`disruptionState`, `budgetEvidence`) and their rendered tests.
4. Apply type/startup/map prerequisites.
5. Apply visual/IA markup and tokens without duplicating lifecycle logic.
6. Apply CX-SOL-001 cursor projection and its regression.
7. Run focused backend truth/degradation tests, frontend typecheck/build and state-specific browser tests.
8. Review actual L1/L2/L3 screenshots; decide separately whether to move the proposal CTA above the map on mobile.

Rollback unit: each semantic layer above. Do not rollback the entire integration to fix a visual issue, and do not accept a green textual merge without the cursor and linked-trigger scenarios.

