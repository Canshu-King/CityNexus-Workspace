# Next Codex Instruction - P1 Route Repair

Continue from the current CityNexus P1 route-repair workspace. Do not reopen C1-C4 and do not render Visio.

## Step 0 - Preserve the official candidate

Before changing anything:

```text
git status --short
sha256 current phase1-routing-rc6-candidate.yaml
```

Do not overwrite the current candidate with any GPT experimental partial file.

## Step 1 - Fix review-workbench reproducibility

Replace the current:

`visio-renderer/calibration/prepare_p1_corridors.py`

with the supplied patched version, or apply `patches/prepare_p1_corridors.diff`.

Place/copy `traveler-corridor-skeleton.yaml` at a supported location or invoke:

```text
python visio-renderer/calibration/prepare_p1_corridors.py --skeleton <actual path>
```

Required reproduction:

```text
abstractGraphPlanar = true
subgraphRouteCount = 12
failures = []
contactPairs = []
globalGeometrySolved = false
```

Do not advance status from this partial result.

## Step 2 - Add the bounded planner as a workbench, not as authority

Place:

`patches/plan_p1_associations.py`

at:

`visio-renderer/calibration/plan_p1_associations.py`

Run a bounded exploration first, for example:

```text
python visio-renderer/calibration/plan_p1_associations.py --trials 80 --global-seconds 120 --per-route-seconds 5 --max-expanded 220000
```

Expected behavior:

- it may exit 2 if incomplete;
- it must not overwrite the official candidate;
- it writes machine-readable trace and an experimental best partial/staging candidate under `calibration/out`.

Do not treat a high solvedCount as a PASS.

## Step 3 - Stop treating route order as the only degree of freedom

External experiments show deterministic shortest-path rerouting can oscillate, especially around:

- `A-M-UC-08`
- `A-CE-09`

and it interacts with:

- `A-PA-07`
- `A-B-06`
- `A-CD-UC-10`
- `A-M-UC-10`

Implement alternate path generation per route.

At minimum generate deterministic candidate families using different corridor biases:

1. shortest/default;
2. top-biased;
3. bottom-biased;
4. inner/left-biased;
5. outer/right-biased.

A candidate family may be implemented by non-negative A* cell penalties or mandatory coarse corridor gates. Do not alter hard obstacles or validators.

## Step 4 - Reserve actor fan-out bands

Planning constraint only:

```text
Traveler source fan-out:
x = 4.4 .. 5.6 cm
horizontal stubs only

Provider source fan-out:
x = 28.0 .. 29.9 cm
horizontal stubs only
```

Do not allow a route to turn vertically inside these bands. This prevents one route from consuming the source ports of all later routes.

## Step 5 - Use mutable super-batches

Do not freeze a route merely because it individually passed.

Super-batch P:

```text
A-M-UC-08
A-CE-09
A-PA-07
A-B-06
```

Super-batch U10:

```text
A-CD-UC-10
A-M-UC-10
A-T-UC-10
A-T-UC-11
```

Traveler backbone and `A-CD-UC-04` / `A-CD-UC-05` stay mutable if a global solution needs movement.

The only truly immutable route geometry is:

```text
EXT-07-06
EXT-09-08
EXT-10-09
```

## Step 6 - Add cycle detection to rip-up/reroute

If the same blocker set repeats for a failed route 2-3 times, do not retry the same shortest-path cost surface.

Record:

```text
failed route
blocker set
route candidate family
expanded states
elapsed time
```

Then switch corridor family or jointly reselect the super-batch.

## Step 7 - Promote only a full candidate

When and only when a complete 18-Association candidate is found:

1. write it to a staging YAML;
2. independently audit all 21 routes;
3. if internal audit is clean, copy to the official candidate;
4. normalize Association waypoints to <=2 decimals;
5. set statuses only after geometry is actually clean;
6. run:

```text
python visio-renderer/calibration/validate_p1_route_candidate_v2.py
python visio-renderer/calibration/validate_p1_route_candidate_v3.py
pytest
```

Required:

```text
V2 PASS
V3 PASS
contactPairCount = 0
uniqueContactCount = 0
crossing = 0
overlap = 0
tjunction = 0
shared_endpoint = 0
shortSegmentCount = 0
redundantCollinearPointCount = 0
complete workspace tests = zero failures
```

Then STOP and create a new external Review Package. Do not render formal Visio or promote RC6 in the same turn.

## Step 8 - New Review Package

Include the normal route candidate, V1/V2/V3 reports, contact audit, worklist, validators, focused tests, full test result, and a real `MANIFEST.json` containing relative path + byte size + SHA-256 for every payload.

Also include:

- the final planner trace;
- route-candidate-family/cycle diagnostics;
- a short statement of which routes were rerouted together.

No stale reports and no `__pycache__` / `.pyc`.
