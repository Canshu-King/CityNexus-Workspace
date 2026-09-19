# Codex next instruction - CityNexus P1 route repair

You are continuing ONLY the P1_UC_Overview Association route-planning repair.

Frozen state:

- C1/C2/C3/C4 = FROZEN_PASS
- EXT-07-06 / EXT-09-08 / EXT-10-09 = immutable C4E1 geometry and semantics
- authoritative candidate must remain unchanged until a complete external-review candidate exists
- RC6 = BLOCKED
- formal Visio render = BLOCKED
- P1 Domain Overview = BLOCKED
- Part 2 = BLOCKED
- codex-chatgpt-web = DEFERRED

## A. Integrate the assist patch safely

1. Run `git status --short` and save it.
2. Verify the authoritative candidate SHA-256 is still:
   `8c1661ebb1a9d5a371f48ef800316dd643f391beec559eb2a4b8065eed75182d`
3. Copy the files under `patches/` into the matching project paths. Do not copy
   any evidence JSON over authoritative project sources.
4. Do not edit Domain, Requirements, Use Cases, semantic page source, C1-C4
   frozen artifacts, or the three Extend routes.
5. Run the focused/full available pytest suite. The assist workspace produced
   `23 passed`.

## B. Prove the topology safety interlock before search

Run/import the common loader against both plans:

- `PLAN_TRAVELER_SKELETON_PROVIDER_GRID` must be rejected immediately with
  genus=1 before routing begins.
- `PLAN_TRAVELER_SKELETON_PLANAR_GRID` must PASS with genus=0.

Any solver entry point that can bypass this interlock must be fixed before
continuing. Never spend search time on genus != 0.

## C. Keep the official candidate failure invariant visible

Rerun V2 and V3 before experiments. Expected current state:

- V2 FAIL
- 46 contact pairs / 55 contacts
- 22 T-junction / 33 shared endpoint
- selfContactCount 0
- 9 short segments
- 88 redundant collinear points
- V3 FAIL only because V2 FAIL; V3 own failures []

If these baseline numbers change before an explicit staging candidate is
created, stop and investigate accidental mutation.

## D. Stop wasting CP-SAT on impossible discrete pools

For every candidate pool use this order:

1. exact self-contact rejection per candidate;
2. route-pair compatibility table;
3. if any pair has compatiblePairs=0 -> synthesize missing families, do NOT run CP-SAT;
4. AC-3 support pruning;
5. if any route domain empties -> perform blocker-bundle family/port repair, do NOT run CP-SAT;
6. cheap MRV first-solution search;
7. CP-SAT only after the discrete pool survives these prechecks.

Report topology plan, topology gate status, genus, candidate counts, impossible
pairs, AC-3 domain sizes, and solver proof/status in every experiment JSON.

Never call a subset “maximum” or “maximal” unless the solver result proves that.
Use `bestObservedDisjointSubset` otherwise.

## E. Immediate target: solve the local UC-06 / UC-07 bundle first

Use:

`visio-renderer/calibration/search_p1_local_bundle_ports.py`

with the validated Traveler skeleton passed explicitly. Start with a bounded
run such as:

```text
python visio-renderer/calibration/search_p1_local_bundle_ports.py ^
  --plan PLAN_TRAVELER_SKELETON_PLANAR_GRID ^
  --traveler-skeleton <path-to-trav-planar-01.yaml> ^
  --variants 30 ^
  --samples 6 ^
  --pair-repair-rounds 2 ^
  --pair-synth-samples 5 ^
  --pair-fixed-limit 5 ^
  --arc-repair-rounds 2 ^
  --arc-synth-samples 8 ^
  --arc-bundle-limit 40 ^
  --seconds 600 ^
  --json-out <diagnostics-path>\local-bundle-search.json
```

`--json-out` is also a progressive checkpoint file: each completed port variant
is persisted during long runs, so a timeout/quota interruption does not erase
the diagnostic work already completed.

The five-route local bundle is:

- A-T-UC-06
- A-T-UC-07
- A-T-UC-11
- A-B-06
- A-PA-07

The provided Traveler skeleton is an OPTIONAL candidate source. It is not a
freeze. The solver may rip it up.

### If AC-3 repeatedly empties T06/T07/B06

Broaden port search in this order:

1. targetSide / targetPortFraction for T06, B06, PA07;
2. then targetSide / targetPortFraction for T07;
3. only then sourcePortFraction for the Traveler cluster.

Every variant must be filtered on the FULL 21-edge rotation system and must
remain genus=0. Do not use local planarity as a substitute for full topology.

The immutable EXT-07-06 U-shaped geometry makes UC-06 a constrained corridor.
Treat T06 and B06 as a joint routing/port-allocation problem, not independent
shortest paths.

## F. Reintegrate only a real local witness

If the local helper returns PASS:

1. save its exact port overrides and candidate polylines as an EXPERIMENTAL
   plan/witness; do not modify the authoritative candidate;
2. run the hardened full topology gate and require genus=0;
3. regenerate the full 18-route pool using the local witness only as optional
   candidates;
4. run pair compatibility -> pair repair -> AC-3 -> bundle repair -> MRV/CP-SAT;
5. require an actual 18/18 contact-free selection.

Pairwise PASS is not global PASS. A 13/18 result is not completion evidence.

## G. Final geometry gate sequence

Only after an 18/18 staging candidate exists:

1. path compression / remove duplicate points;
2. collapse collinear points;
3. normalize coordinates to <=2 decimals;
4. no segment <0.10 cm;
5. exact cross-route contacts = 0;
6. exact self-route contacts = 0;
7. no unrelated-node traversal;
8. endpoint tangency PASS;
9. V1 PASS;
10. Contact Audit PASS;
11. V2 PASS;
12. set metadata/status fields exactly as previously specified;
13. V3 PASS;
14. full pytest zero failures.

At the FIRST all-green result: STOP.

Do NOT in that same run:

- render formal Visio
- promote/generate RC6
- start P1 Domain Overview
- start Part 2
- install or configure codex-chatgpt-web

Create a new review ZIP with MANIFEST (relative path, size, SHA-256), fresh
reports, fresh tests, staging YAML, topology report, and no cache files, then
return it for external GPT freeze review.
