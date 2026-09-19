# Codex Next Instruction: Topology-Aware Global Association Router

Stay in the current stage only: `P1_UC_Overview Association route repair`.

Frozen:

- C1/C2/C3/C4 = FROZEN_PASS
- `EXT-07-06`, `EXT-09-08`, `EXT-10-09` = immutable
- Association `id`, `connectorType`, `source`, `target` = immutable
- RC6 / formal Visio / P1 Domain / Part 2 / codex-chatgpt-web = blocked

## 0. Preserve the official candidate

Before work:

1. `git status --short`
2. hash `visio-renderer/phase1-routing-rc6-candidate.yaml`
3. do all experiments in staging/out files
4. do not overwrite the official candidate until a complete staging candidate has passed exact internal audit.

## 1. Integrate the hardened topology pre-gate

Copy:

- `patches/audit_p1_route_topology_v2.py`
- existing `P1_ROUTE_PORT_PLANS.yaml`

into `visio-renderer/calibration/`.

Reproduce:

- current -> genus 2 FAIL
- PLAN_O -> genus 0 PASS
- PLAN_R -> genus 0 PASS

The new gate must reject any plan override that changes fields other than:

- `sourcePortFraction`
- `targetSide`
- `targetPortFraction`

It must reject every Extend override.

Use `PLAN_O_PRESERVE_LOCAL_GEOMETRY` as the first geometry seed. PLAN_R is fallback only after a bounded PLAN_O candidate-family search is exhausted.

## 2. Fix the geometry representation before more A*

Do not use `_raster_segment()` as the only occupancy truth.

Reason: valid endpoint/stub coordinates include 3.16, 4.23, 8.875, 11.225, 12.575 cm. The old 0.10-only raster silently drops segments on these constant coordinates.

Integrate `patches/critical_grid_geometry.py`.

Also integrate `patches/route_candidate_selector.py` after family generation. It precomputes exact pairwise candidate conflicts and performs MRV/forward-checking selection, so generated routes are not frozen simply because they were found first. Keep it as an internal planner helper; official V2/V3 remain the authority.

Build a critical-coordinate rectilinear graph containing:

- 0.10 cm coarse interior lattice;
- exact node left/right/top/bottom coordinates;
- exact frozen Extend coordinates;
- exact source/target port coordinates;
- +/-0.10 cm offset lanes around critical coordinates;
- page boundaries.

All collision accounting must use exact quantized coordinates or exact closed-segment checks.

## 3. Replace permanent greedy routing with candidate-family selection

Do not make accepted routes permanent hard obstacles during the main search.

For each route generate at least 5 real homotopy families:

- default
- top_outer
- bottom_outer
- inner_left
- outer_right
- mandatory_gate where required

Generate 1-3 deterministic alternatives inside each family.

A family is not just a soft cost bias. A mandatory-gate family must force passage through a coarse gate rectangle/line so it represents a different homotopy class.

Use `P1_ROUTE_FAMILY_SEEDS.yaml` as planning hints.

## 4. Search one candidate per route as a compatibility problem

For every generated candidate:

- verify orthogonality;
- verify endpoint tangency;
- verify no unrelated-node interior traversal;
- verify no frozen-Extend contact;
- verify no self-contact;
- verify every compressed segment >= 0.10 cm.

Then precompute pairwise exact contact conflicts between route candidates.

Select candidates with an interleaved beam / backtracking CSP:

- joint mutable core:
  - A-M-UC-08
  - A-CE-09
  - A-PA-07
  - A-B-06
  - A-CD-UC-10
  - A-M-UC-10
  - A-T-UC-10
  - A-T-UC-11
- beam width: start 64
- expand top K: 6
- next route: MRV, then blocker degree
- keep A-CD-UC-04 / A-CD-UC-05 preferred but mutable

If a state repeats the same:

`portPlan + familyVector + failedRoute + blockerSet`

then do not retry the same cost surface. Add/choose another mandatory-gate family or boundedly change allowed port fields, then re-run topology pre-gate.

## 5. PLAN_O-specific geometry priorities

Under PLAN_O:

- A-T-UC-10 belongs on the left side of frozen EXT-10-09 at UC-10.
- A-M-UC-10 belongs on the right-side pocket; include a bottom-right entry family.
- A-CD-UC-10 also needs a true outer/bottom family; do not force a direct x=27 crossing inside y=9.4..14.2.
- A-M-UC-08 has a useful right/bottom entry because its UC-08 target is right of the frozen x=11.1 terminal leg.
- A-B-06 and A-PA-07 require distinct upper-mid lanes.
- A-CE-09 needs an outer-bottom/left alternative around UC-12.

Do not hard-freeze CD04/CD05 just because they were clean in the old candidate.

## 6. Only after a full 18-Association staging candidate exists

Normalize:

- duplicate points removed;
- collinear points collapsed;
- waypoints <=2 decimal places;
- each segment >=0.10 cm.

Run exact staging audit before touching the official candidate.

Then, and only if staging is clean, copy it to the official candidate and set:

- metadata.status = `GEOMETRY_PASS_PENDING_EXTERNAL_FREEZE`
- all 18 Association planningStatus = `ROUTE_PLANNED_PENDING_EXTERNAL_FREEZE`
- three Extends remain `FROZEN_FROM_C4E1`

Run:

- `validate_p1_route_candidate.py`
- `audit_p1_route_contacts.py`
- `validate_p1_route_candidate_v2.py`
- `validate_p1_route_candidate_v3.py`
- complete `pytest`

Required: every defect count zero, V2 PASS, V3 PASS, pytest zero failures.

## 7. First full PASS = hard stop

Immediately STOP.

Do not render Visio, do not produce RC6, do not start P1 Domain, Part 2, or codex-chatgpt-web.

Create a new external Review Package containing:

- candidate YAML
- V1/V2/V3 reports
- contact audit
- worklist
- topology report + selected port plan
- planner trace
- candidate-family / conflict diagnostics
- validators + focused tests
- full-test result
- `MANIFEST.json` with relative path + byte size + SHA-256 for every payload

No stale reports, `__pycache__`, or `.pyc`.
