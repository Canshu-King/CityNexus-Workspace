# P1 Route Topology Findings — 2026-09-07

## What changed in the diagnosis

The current V2 failure is not merely 55 bad contact points. An independent
rotation-system audit of the uploaded candidate shows a stronger invariant:

- current candidate: `V=16, E=21, F=3`
- orientable genus: `g=(2-V+E-F)/2 = 2`
- result: **topologically non-planar port ordering**

That means a waypoint-only A* planner can keep moving contacts around forever.
Before maze routing, the source/target port ordering itself must be changed.
This is within the already-approved repair scope because Association
`sourcePortFraction`, `targetSide`, `targetPortFraction`, and `waypoints` are
modifiable; connector identity and the three C4E1 Extends remain frozen.

## Concrete source of the contradiction

The uploaded Traveler right-side order is approximately:

`UC05, UC04, UC02, UC11, UC06, UC08, UC07, UC10, UC12`

The `UC06-UC07` triangle block is split by `UC08`, and the City-Data / Mobility
cyclic orders are not simultaneously compatible with that rotation system.
This is a topology problem, not a micro-dogleg problem.

## Two genus-0 seeds

`P1_ROUTE_PORT_PLANS.yaml` contains two independently checked genus-0 seeds.

- `PLAN_O_PRESERVE_LOCAL_GEOMETRY`: minimal/local change. Keeps the two clean
  City-Data relations as geometry obstacles, moves CD10 between their actor
  ports, swaps the Traveler T07/T08 ordering, and uses locally natural target
  sides around UC04/UC08/UC10.
- `PLAN_R_REVERSE_EMBEDDING`: alternative planar embedding. In a provisional
  negotiated-congestion experiment it reached a lower residual grid-conflict
  count, but can force longer detours around the fixed top-right geometry.

Neither seed is a freeze candidate. They are topology-safe starting points.

## New planner order

1. **Topology pre-gate**: rotation genus must be 0 and no two unrelated routes
   may share the same node perimeter position.
2. Build a planar face/rotation scaffold from the selected port plan.
3. Route Associations globally. Do not permanently freeze each greedy shortest
   path. Use negotiated congestion or rip-up/backtracking and preserve the face
   rotation/homotopy.
4. Compress collinear points, normalize to <=2 decimals, remove micro-jogs.
5. Run unchanged V2 and V3.
6. First `pytest=0`, `V2=PASS`, `V3=PASS` => STOP and package for external GPT
   freeze. Do not render RC6 in that same iteration.

## What not to do

- Do not touch `EXT-07-06`, `EXT-09-08`, `EXT-10-09`.
- Do not reopen C1-C4.
- Do not weaken `contactPairCount == 0`.
- Do not return to 0.02/0.03/0.05 cm patch doglegs.
- Do not install `codex-chatgpt-web` before route freeze.
