# Provider Runtime Freeze Gate

Do not freeze Provider Runtime until all of the following are true in the real
worktree.

## Existing gate

- PRT-01 same Generate Replan operation uses one frozen snapshot.
- PRT-02 real provider provenance is persisted.
- PRT-03 fallback is pair-scoped and auditable.
- PRT-04 no fact is produced when primary and fallback both fail.
- PRT-05 deterministic feasibility never calls a live provider.
- PRT-06 JourneyTwin GET never performs provider capture.
- PRT-07 offline Golden Scenario remains operational.
- PRT-08 Valhalla MockTransport -> snapshot -> gate works.

## External hardening gate

- PRH-01 snapshot facts are structurally immutable.
- PRH-02 Twin reports the effective fact provider and separately identifies the
  snapshot's source provider.
- PRH-03 degraded mobility propagates into FeasibilityEnvelope and verified
  robustness scoring.
- PRH-04 base and candidate travel delta are computed under the same frozen
  mobility reality.
- PRH-05 accept-time feasibility uses explicit frozen mobility evidence and does
  not silently default to mock.

## Regression gate

- provider + hardening focused tests: zero failures.
- full backend: zero failures except the opt-in live Valhalla skip.
- compileall: PASS.
- Ruff: PASS in the user's configured environment.
- OpenAPI formal/runtime parity: 38/38 unless an intentional contract change is
  made and both sides are updated.
- frontend build: PASS.
- backend-connected Playwright Golden Scenario: PASS.
- offline/no-network Golden Scenario: PASS.

## Hard stop

When the above passes, mark:

```text
Provider Runtime Gate = FROZEN_PASS
```

Then move to Open-Meteo runtime weather-to-Activity mapping. Do not start
OR-Tools, AI, MapLibre polish or Visio in the same mutation batch.
