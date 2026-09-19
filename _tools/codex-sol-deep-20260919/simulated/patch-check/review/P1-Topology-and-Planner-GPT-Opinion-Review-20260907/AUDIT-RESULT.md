# Audit Result

## Verdict

The official candidate is not ready for status advancement. The prior route
planning is blocked first by a non-planar port rotation, then by an incomplete
global routing strategy.

## Verified Reproduction

- Official candidate topology: `V=16`, `E=21`, `F=3`, `genus=2`, FAIL.
- `PLAN_O_PRESERVE_LOCAL_GEOMETRY`: `V=16`, `E=21`, `F=7`, `genus=0`, PASS.
- `PLAN_R_REVERSE_EMBEDDING`: `V=16`, `E=21`, `F=7`, `genus=0`, PASS.
- The official candidate used for reproduction has SHA-256
  `8C1661EBB1A9D5A371F48EF800316DD643F391BEEC559EB2A4B8065EED75182D`.
- V2 rerun reports 46 route-pair contacts, 55 unique contacts, 9 short
  segments, and 88 redundant collinear points.
- V3 rerun reports FAIL because V2 FAILs; its independent frozen-route checks
  contain no failures.
- Existing full test evidence is `51 passed in 0.27s`.

## Interpretation

The topology finding is stronger than a routing-order heuristic. The current
ports induce a genus-2 rotation system, so a waypoint-only A* search under that
ordering has no zero-contact planar destination. The genus-0 plans are search
seeds, not replacement candidates or frozen truth.

The planner aid contributes valid routing ideas but needs integration after the
topology pre-gate. Its existing sequential occupancy algorithm can reproduce
deadlocks because accepted routes become hard obstacles. The reported
`A-M-UC-08` / `A-CE-09` oscillation is expected until candidate families and
batch-level rip-up/backtracking are added.

## Prohibited During This Repair

- Change any of `EXT-07-06`, `EXT-09-08`, or `EXT-10-09`.
- Alter validator rules or contact tolerances.
- Promote an experimental partial output to the official candidate.
- Render formal Visio, promote RC6, or begin Part 2.

## Exit Gate

`pytest` must have zero failures; Base Gate, Contact Audit, V2, and V3 must
pass; proper crossings, overlaps, contacts, T-junctions, shared endpoints,
short segments, and redundant collinear points must all equal zero.
