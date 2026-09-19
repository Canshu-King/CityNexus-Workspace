# Weather Runtime Freeze Gate

Weather Runtime can be declared `FROZEN_PASS` only if all of the following are true.

## WRT acceptance tests

- WRT-01 Open-Meteo Unix UTC MockTransport contract PASS
- WRT-02 Journey timezone mapping PASS
- WRT-03 deterministic time intersection PASS
- WRT-04 exact query scope evidence PASS
- WRT-05 explicit indoor/outdoor sensitivity PASS
- WRT-06 execution-state filter PASS
- WRT-07 public trusted-provenance forgery rejection PASS
- WRT-08 repeated polling idempotency PASS
- WRT-09 outage -> degradation, no fake weather PASS
- WRT-10 recovery resolves degradation PASS
- WRT-11 C4 remains durable under weather attribution PASS
- WRT-12 offline Closure Golden regression PASS

## Regression gates

The old gates must remain green:

- Provider Runtime PRT-01..PRT-08
- Provider Runtime Hardening PRH-01..PRH-05
- Backend Golden Scenario
- full backend pytest
- compileall
- Ruff on the real Windows/dev environment
- OpenAPI parity if any endpoint is added/changed
- frontend build / Playwright if the weather trigger touches frontend/API

## Architectural assertions

- provider calls are outside deterministic feasibility
- no live Open-Meteo in GET/Twin read paths
- no AI Activity attribution
- no fabricated weather on provider failure
- server owns `PROVIDER_VERIFIED`
- weather facts are frozen before Event ingestion
- Activity attribution is deterministic and auditable
- C4 remains authoritative

## Hard stop

When this gate passes, package a fresh review checkpoint and stop. Do not silently start OR-Tools in the same mutation batch.
