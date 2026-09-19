# Track A — Integration / release readiness

Produce:
- `reports/INTEGRATION_CHANGE_MAP.md`
- `reports/INTEGRATION_RISK_REGISTER.md`
- `reports/OWNER_ACTION_SEQUENCE.md`
- `reports/ROLLBACK_AND_REPRO_PLAN.md`

Inspect read-only:
- integration commit graph / detached state;
- dirty and untracked files;
- Qoder v6 truth handoff;
- Apple frontend handoff;
- divergence from `D:\moodle\CityNexus`;
- existing status/release docs.

Classify deltas:
- truth/backend
- frontend visual/IA
- frontend prerequisite type/behavior
- test-only
- evidence/tooling
- environment-only

For each risky overlap record:
file, competing behavior, recommended winner, reconciliation rule, gates to rerun.
No source edits.
