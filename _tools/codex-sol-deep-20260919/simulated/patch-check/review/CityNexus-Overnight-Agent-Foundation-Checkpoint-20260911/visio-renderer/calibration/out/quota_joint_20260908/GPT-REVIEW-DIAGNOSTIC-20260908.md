# CityNexus P1 Route Repair V3 — GPT Diagnostic Review Package

Date: 2026-09-08

## Scope and safety

- Official candidate was not modified.
- RC6 was not promoted.
- No Visio render was performed.
- Frozen Extend IDs remain immutable: `EXT-07-06`, `EXT-09-08`, `EXT-10-09`.
- Validators were not weakened.

## Topology result

`PLAN_QUOTA_SAVER_NEAR8_PORTS_20260908` passed the topology pre-gate with `V=16`, `E=21`, `F=7`, `orientableGenus=0`.

## Search results

- 24-way seven-route hard search: all workers failed at best `6/7`.
- 24-way eight-route hard search: all workers failed at best `7/8`.
- 24-way negotiated/rip-up search: all workers routed `8/8`, but the best exact resource result retained two conflicting vertices, principally among `A-B-06`, `A-CD-UC-10`, and `A-M-UC-10`.
- Exact candidate-pool/CSP search with the official partial fixed seed produced 579 candidates. Pairwise precheck passed, but AC-3 became empty for `A-CD-UC-10`; the dominant blockers were `A-B-06` and `A-PA-07`, with `A-M-UC-10` also recurring.

## Current blocker

The near8 port rotation is genus-zero, but the current route candidate pool has no globally supported `A-CD-UC-10` candidate after contact-free pruning. This is a port/corridor compatibility blocker, not evidence that the validator is too strict or that the official candidate should be overwritten.

## Recommended next experiment

Search a new genus-zero port allocation for the coupled set `A-CD-UC-10`, `A-B-06`, `A-PA-07`, `A-M-UC-10`, while retaining the frozen Extend fields and the validated Traveler seed. Then regenerate candidate pools and rerun topology pre-gate → Contact Audit → V2 → V3 → full pytest.

## Included evidence

- `near8-topology.json`
- `near8-pool.json`
- `near8-best-witness.json`
- `seven-hard-*.json` and `eight-hard-*.json`
- `near8-negotiated-*.json`
- `P1_ROUTE_PORT_PLANS.yaml`
- exploratory search and rip-up scripts used in this round
