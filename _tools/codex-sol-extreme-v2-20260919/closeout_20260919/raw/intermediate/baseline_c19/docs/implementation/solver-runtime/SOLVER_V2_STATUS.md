# Solver V2 Status

Status: **INTEGRATED / deterministic local gate green**

Solver V2 is an incremental whole-horizon capability. The proven Solver V1
single-slot path remains the default for `CITYNEXUS_SOLVER=deterministic`,
`ortools`, and `auto`. Setting `CITYNEXUS_SOLVER=v2` enables the multi-slot
path through the existing `POST /api/v1/journeys/{journey_id}/replans`
contract.

The V2 core consumes only primitive facts in `SolverV2Problem`:

- remaining mutable slots and server-owned alternatives;
- protected C4 anchors;
- opening windows, costs, preference fit, and disruption risk penalties;
- a frozen MobilitySnapshot matrix;
- Journey budget and schedule horizon.

`solve_v2()` produces deterministic Top-K plans. It supports keep, replace,
and drop assignments, fixed-sequence whole-horizon scheduling, protected-anchor
buffers, opening-hour windows, budget ceilings, schedule drift, risk penalties,
and stable fingerprints. Missing frozen travel facts make a branch unavailable;
they are never treated as zero travel.

Every V2 plan is materialized as a normal `PlanVersion` and passes the existing
CityNexus deterministic feasibility gate before it becomes a `PRESENTED`
proposal. The accept endpoint still performs its ordinary revalidation. Solver
V2 therefore proposes schedules; CityNexus remains the authority for business
facts and post-action feasibility.

Evidence:

- pure V2 contract and objective tests: `backend/tests/test_solver_v2.py`;
- endpoint materialization and acceptance: `backend/tests/test_solver_v2_integration.py`;
- existing V1 policy, post-gate, provenance, and optional-boundary suites remain green.

This is a deterministic product/demo implementation of the V2 contract. The
enumeration core is intentionally replaceable by CP-SAT without changing the
frozen-input or materialization boundary.
