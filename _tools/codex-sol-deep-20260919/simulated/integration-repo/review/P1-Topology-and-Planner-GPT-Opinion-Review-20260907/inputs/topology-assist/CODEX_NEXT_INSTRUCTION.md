# Next Codex instruction

Work only on **P1_UC_Overview Association route planning repair**.

Frozen baseline remains:

- C1/C2/C3/C4 = FROZEN_PASS
- `EXT-07-06`, `EXT-09-08`, `EXT-10-09` = immutable C4E1 geometry
- RC6 = BLOCKED
- Part 2 = BLOCKED
- `codex-chatgpt-web` = DEFERRED

## New externally discovered blocker

Before writing more A*, add and run `audit_p1_route_topology.py`.
The current candidate's port rotation is topologically non-planar (orientable
**genus 2**). Therefore waypoint-only repair cannot reach zero contact while
those port orders remain.

Treat this topology check as a pre-gate before V2/V3. It does not replace V2/V3.

## Required implementation sequence

1. Copy `audit_p1_route_topology.py` and `P1_ROUTE_PORT_PLANS.yaml` into
   `visio-renderer/calibration/`.
2. Reproduce current-candidate topology FAIL (genus 2).
3. Reproduce genus-0 PASS for both supplied plans without changing the three
   Extend routes.
4. Use the two plans as search seeds, not as frozen truth. Prefer the plan that
   minimizes route length/bends while still reaching V2=PASS.
5. Upgrade the Association planner so it searches **topology first, geometry
   second**:
   - reject any port allocation with genus != 0 before A*;
   - preserve the selected clockwise rotation/face structure;
   - use global negotiated congestion or rip-up/backtracking;
   - do not permanently hard-freeze each newly found greedy route;
   - if a lane dead-ends, change port fraction/side within the same planar
     rotation or rip up a conflicting set; never weaken V2.
6. After path compression, enforce <=2 decimal coordinates and no segment
   shorter than 0.10 cm.
7. Run full tests + original gate + Contact Audit + V2 + V3.

Final acceptance remains exactly:

```text
pytest = zero failures
V2 = PASS
properCrossingCount = 0
collinearOverlapPairCount = 0
contactPairCount = 0
uniqueContactCount = 0
crossing = 0
overlap = 0
tjunction = 0
shared_endpoint = 0
shortSegmentCount = 0
redundantCollinearPointCount = 0
V3 = PASS
```

On the first all-green result:

- set metadata/status exactly as previously specified;
- STOP;
- do not render formal Visio or generate RC6 in the same turn;
- create a fresh external-review ZIP with manifest/hash and no stale reports.
