# CityNexus P1 Topology + Planner External Review Findings

Date: 2026-09-07
Scope: `P1_UC_Overview` Association route repair only.

## 1. Verdict

The review package is directionally correct and materially improves the diagnosis, but it is **not yet a geometry candidate** and its supplied planner must not be promoted unchanged.

The strongest finding is reproduced independently:

- current port rotation: `V=16, E=21, F=3, genus=2` -> non-planar rotation, FAIL;
- `PLAN_O_PRESERVE_LOCAL_GEOMETRY`: `V=16, E=21, F=7, genus=0` -> topology pre-gate PASS;
- `PLAN_R_REVERSE_EMBEDDING`: `V=16, E=21, F=7, genus=0` -> topology pre-gate PASS.

The official candidate is byte-for-byte unchanged relative to the earlier route-repair package and remains V2/V3 FAIL.

## 2. Package audit

Verified on the uploaded ZIP:

- ZIP SHA-256: `0acebae96da413492271a9ff3c31d6f6abaf7b06917378610645ddbccec53caf`
- 41 ZIP entries: 40 files + 1 directory;
- ZIP CRC test: PASS;
- duplicate paths: 0;
- unsafe `..` / absolute paths: 0;
- symlinks: 0;
- **`MANIFEST.json` is missing**.

The missing manifest is a packaging/traceability defect. It does not invalidate the topology result, but the next external review package should restore the normal relative-path + byte-size + SHA-256 manifest contract.

## 3. Reproduction

Focused tests from the prior self-contained review package reproduce `8 passed`. The new package carries only the text evidence `51 passed in 0.27s`; the complete 51-test workspace is not present, so that figure remains evidence rather than independently replayable proof from this ZIP alone.

Re-running the current validators gives the same blocker:

- V1 historical gate: PASS;
- V2: FAIL;
- contact-pair count: 46;
- unique contacts: 55;
- T-junctions: 22;
- shared endpoints: 33;
- short segments: 9;
- redundant collinear points: 88;
- V3: FAIL only because V2 FAIL; V3's own frozen-Extend failures list is empty.

## 4. Topology audit review

The topology conclusion is sound for this graph. I independently recomputed the face cycles using route-ID darts rather than neighbour lookup and obtained the same genus values: current=2, PLAN_O=0, PLAN_R=0.

The supplied `audit_p1_route_topology.py` is adequate for the current simple graph, but it should be hardened before becoming a permanent gate:

1. plan overrides should be rejected unless they change only:
   - `sourcePortFraction`
   - `targetSide`
   - `targetPortFraction`
2. an override must never target an Extend route;
3. face tracing should use route-ID darts, not `rotation[b].index(a)`, so the code remains correct if parallel edges ever appear;
4. the report should expose edge-to-face incidence for a face-aware router.

A hardened drop-in pre-gate is supplied as `patches/audit_p1_route_topology_v2.py`.

## 5. Critical planner correctness bug: 0.10 cm raster blind spot

This is the most important implementation defect found in the supplied bounded A* planner.

`_raster_segment()` records a horizontal segment only when its Y coordinate is exactly on the 0.10 cm grid, and records a vertical segment only when its X coordinate is exactly on that grid. If the constant coordinate is off-grid, the function silently returns an empty occupancy set for that segment.

The actual P1 geometry contains legal terminal coordinates that are not 0.10-aligned, including:

- `3.16 cm`
- `4.23 cm`
- `8.875 cm`
- `11.225 cm`
- `12.575 cm`

Therefore a route segment on one of those coordinates can be invisible to the planner's occupancy map. A later route can geometrically contact it while the sequential occupancy search believes the space is free. The final exact V2 audit would catch the defect, but the search itself wastes work and can falsely believe a partial state is conflict-free.

Conclusion:

> 0.10 cm is suitable as a coarse interior planning lattice, but it is not sufficient as the sole proof geometry representation.

Recommended fix:

- construct a critical-coordinate rectilinear graph containing the coarse lattice **plus** exact node boundaries, exact frozen-Extend coordinates, exact terminal ports, and +/-0.10 cm offset lanes;
- or quantize exact geometry at 0.005 cm for collision accounting while retaining a coarser search graph;
- run exact closed-segment contact checks on every complete candidate before V2.

`patches/critical_grid_geometry.py` supplies the exact integer-coordinate primitives and critical-coordinate collector.

A second helper, `patches/route_candidate_selector.py`, is also supplied. It does not pretend to solve path generation; it takes several deterministic family candidates per Association, builds an exact pairwise contact-conflict graph, and selects one candidate per route with MRV + forward-checking/backtracking. This directly replaces the dangerous "first route wins forever" selection rule while keeping path generation and official validation separate. Its bundled tests include both a solvable joint-conflict case and an unsatisfied blocker case.

## 6. PLAN_O vs PLAN_R

Recommendation: **use PLAN_O as the first full geometry seed; keep PLAN_R as a bounded fallback.**

This is not merely because PLAN_O preserves more local geometry. The frozen Extend topology makes two PLAN_O endpoint assignments materially friendlier:

### UC-10

Frozen `EXT-10-09` leaves its UC-10 top port at `x=23.3`.

Under PLAN_O:

- Traveler `A-T-UC-10` targets the UC-10 top at approximately `x=22.3`, on the **left** side of the frozen Extend;
- Mobility `A-M-UC-10` targets approximately `x=24.3`, on the **right** side.

That matches the source geography: Traveler starts on the left of the page, Mobility on the right.

PLAN_R swaps those two sides. It therefore forces the left-origin Traveler route into the right-side frozen-Extend pocket and the right-origin Mobility route toward the left side.

### UC-08

Frozen `EXT-09-08` reaches the UC-08 bottom at `x=11.1`.

Under PLAN_O, `A-M-UC-08` targets about `x=11.9`, on the right side of that terminal leg.

Under PLAN_R, `A-M-UC-08` targets about `x=9.9`, inside the left-bottom pocket. A right-origin Mobility route must then detour around the frozen U-shaped Extend geometry to enter that pocket.

In a bounded independent critical-grid experiment, this manifested exactly as expected: PLAN_R produced only one easy `A-M-UC-08` family under a small family set, and that route acted as a long barrier that conflicted with every generated `A-B-06` candidate. PLAN_O produced several locally valid `A-M-UC-08` alternatives under the same style of family generation. This is diagnostic evidence, not an official gate result.

PLAN_O still has a cost: `A-CD-UC-10` sits between the two City-Data source ports used by the currently clean CD04/CD05 routes, so the City-Data group must not be hard-frozen. That is a smaller, more localized search problem than PLAN_R's two frozen-pocket reversals.

## 7. Do not use route-order randomization as the main search dimension

The supplied `plan_p1_associations.py` still solves one route, marks its occupied cells as hard obstacles, and proceeds sequentially. Random trials change only route order. That is not enough for this instance.

The correct next solver is a **candidate-family CSP / beam search**:

1. pick a genus-0 port plan;
2. generate K deterministic homotopy/corridor candidates per mutable route;
3. exact-audit each single-route candidate against nodes + frozen Extends;
4. precompute pairwise route-candidate conflicts;
5. select one candidate per route by MRV/beam/backtracking;
6. if no combination exists, generate more families only for the routes in the minimal blocker set;
7. optionally allow bounded port-fraction/side changes, but every changed port allocation must re-run the topology pre-gate before geometry search.

This turns the problem from repeated greedy maze routing into a finite compatibility search.

## 8. Super-batch strategy

Do **not** solve P completely, freeze it, and then solve U10. They share the same right/bottom bottlenecks around frozen `EXT-10-09`.

Use an interleaved beam over the joint mutable core:

- P: `A-M-UC-08`, `A-CE-09`, `A-PA-07`, `A-B-06`
- U10: `A-CD-UC-10`, `A-M-UC-10`, `A-T-UC-10`, `A-T-UC-11`

Suggested beam settings for the first implementation:

- beam width: 64;
- retain top 6 candidates per expanded route;
- choose next route by MRV (fewest currently compatible candidates), then by blocker degree;
- candidate score: path length + bend penalty + narrow-corridor penalty;
- repeat signature: port plan + selected family vector + failed route + blocker set.

`A-CD-UC-04` and `A-CD-UC-05` should be *preferred anchors*, not immutable geometry. Only the three Extend routes are truly frozen.

## 9. Candidate families must include mandatory gates

The current `top/bottom/left/right` soft biases are too weak. Several routes require a topologically different homotopy, not a slightly different shortest path.

Examples are encoded in `P1_ROUTE_FAMILY_SEEDS.yaml`. Important cases include:

- `A-M-UC-10` / `A-CD-UC-10`: right-pocket / bottom-entry families around the frozen EXT10 U-shape;
- `A-M-UC-08`: a bottom/right entry family relative to frozen EXT09;
- `A-CE-09`: an outer-bottom/left family around UC-12;
- `A-B-06` and `A-PA-07`: separate upper-mid crossing lanes;
- `A-T-UC-10`: stay on the left side of the frozen UC-10 Extend port under PLAN_O.

A mandatory gate means the route must pass through a coarse gate rectangle/line before reaching the target. This creates genuinely different homotopy classes. Merely adding a small Y/X bias often returns the same class again.

## 10. Exit gate remains unchanged

No lowering of the gate is justified.

Promotion still requires:

- full workspace pytest: zero failures;
- Base Gate PASS;
- Contact Audit PASS;
- V2 PASS;
- V3 PASS;
- proper crossings = 0;
- collinear overlaps = 0;
- contact pairs = 0;
- unique contacts = 0;
- T-junctions = 0;
- shared endpoints = 0;
- short segments = 0;
- redundant collinear points = 0;
- all three Extend routes unchanged.

At the first full PASS, stop and create an external review package. Do not render formal Visio or promote RC6 in the same run.
