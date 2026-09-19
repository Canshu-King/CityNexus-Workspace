# CityNexus P1 Route Repair V3 - GPT Aid Package

Date: 2026-09-07

This package is an **engineering aid for Codex**, not a frozen route solution and not an RC6 deliverable.

## What GPT independently verified

The supplied `CityNexus-P1-Route-Repair-V3-GPT-Opinion-20260907-continued.zip` was unpacked and exercised locally.

Current official candidate remains unchanged:

- historical base gate: PASS
- Contact Audit: FAIL
- V2: FAIL
- V3: FAIL because V2 fails; V3 own frozen-contract failures remain empty
- current defects remain 46 contact pairs / 55 unique contacts / 22 T-junctions / 33 shared endpoints / 9 short segments / 88 redundant collinear points
- focused tests in the review package reproduce 8 passed / 0 failed
- the package records 51 passed / 0 failed for the full workspace, but that full suite is not contained in the review ZIP

## Concrete defect fixed here

The review ZIP's `prepare_p1_corridors.py` is not self-contained. It hardcodes:

`ROOT.parent / 'handoff_20260907/traveler-corridor-skeleton.yaml'`

That path does not exist in the review package, even though `traveler-corridor-skeleton.yaml` is present at package root.

`patches/prepare_p1_corridors.py` fixes this by:

1. accepting `--skeleton PATH`;
2. searching project-root/package-friendly locations first;
3. preserving the old `handoff_20260907` path as a compatibility fallback;
4. recording the resolved skeleton path in the validation report.

The fixed script was executed successfully against the supplied skeleton and reproduced:

- `abstractGraphPlanar = true`
- `subgraphRouteCount = 12`
- `failures = []`
- `contactPairs = []`
- `globalGeometrySolved = false`

## New bounded planner prototype

`patches/plan_p1_associations.py` is a pure-Python 0.10 cm orthogonal planning workbench.

It deliberately:

- does **not** call Visio/COM;
- treats the 3 C4E1 Extend routes as immutable hard obstacles;
- searches all four target sides;
- allows source/target port-fraction changes without changing semantic identity;
- reserves source fan-out bands so one early route cannot vertically block every other port on a shared actor;
- has per-route state limits, per-route deadlines, a global deadline, and bounded trial count;
- writes staging/best-partial output under `calibration/out` only;
- never overwrites `phase1-routing-rc6-candidate.yaml`;
- returns exit code 2 when search is incomplete instead of pretending success.

A short smoke run intentionally remained incomplete and produced a best partial of 9/18 Associations. This is useful evidence that the workbench is bounded and honest, not evidence of completion.

## Important new routing finding

The current problem is **not just route order**.

Experiments reached:

- 8/9 Provider Associations in one contact-free sequential partial, with only `A-CD-UC-10` left unroutable;
- removing any single already-routed Provider did not make that final route globally recoverable;
- removing either `{A-PA-07, A-CE-09}` or `{A-M-UC-10, A-M-UC-08}` allowed `A-CD-UC-10` to route, but the removed pair could not then be reinserted by the same deterministic shortest-path strategy;
- naive rip-up/reroute falls into a repeatable `A-M-UC-08 <-> A-CE-09` oscillation.

Therefore Codex should **not** keep changing only route order while using the same single shortest path per route. It needs alternate homotopy/corridor candidates or joint batch search.

## New source-egress reservation recommendation

Reserve these planning-only fan-out zones:

- Traveler: `x = 4.4 .. 5.6 cm`, horizontal source stubs only;
- right-side Provider actors: `x = 28.0 .. 29.9 cm`, horizontal source stubs only.

Do not allow unrelated vertical route segments inside those zones. This prevents one route from consuming every remaining source port, a failure observed in sequential searches.

## Useful individual routes, not globally frozen

Against the 3 frozen Extend routes alone, the bounded planner found simple examples such as:

`A-B-06`:

`(29.9, 9.0) -> (13.3, 9.0) -> (13.3, 8.875)` using `UC-06 BOTTOM`.

`A-M-UC-08`:

`(29.9, 8.0) -> (27.1, 8.0) -> (27.1, 14.3) -> (13.3, 14.3) -> (13.3, 12.575)` using `UC-08 BOTTOM`.

`A-CE-09`:

`(29.9, 14.3) -> (17.1, 14.3) -> (17.1, 12.575)` using `UC-09 BOTTOM`.

These are **diagnostic corridor references only**. In particular, `A-M-UC-08` and `A-CE-09` must not both be frozen from those independent shortest paths because their interaction causes a deadlock/oscillation.

## Files

- `CODEX-NEXT-INSTRUCTIONS.md` - exact next-step instructions.
- `EXPERIMENT-NOTES.md` - detailed external findings.
- `patches/prepare_p1_corridors.py` - self-contained path fix.
- `patches/prepare_p1_corridors.diff` - minimal patch.
- `patches/plan_p1_associations.py` - bounded global A* workbench.
- `PREPARE-FIX-TEST.txt` - successful reproduction output.
- `PLANNER-SMOKE-RESULT.txt` - bounded planner smoke result.
- `P1-ASTAR-PLANNER-TRACE.json` - smoke-run machine-readable trace.
- `P1-ASTAR-BEST-PARTIAL.yaml` - experimental partial only; never render/freeze it.

## Hard stop remains unchanged

Do not render Visio, promote RC6, begin P1 Domain Overview, begin Part 2, or install `codex-chatgpt-web` until the official route candidate passes V2 and V3 with all defect counts zero and the complete workspace test suite passes.
