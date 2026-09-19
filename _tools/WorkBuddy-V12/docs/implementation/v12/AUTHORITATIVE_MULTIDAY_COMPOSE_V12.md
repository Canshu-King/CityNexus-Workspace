# V12 Authoritative Multi-day Compose

`compose_authoritative_multiday` is the V12 composition path.

- User-selected POIs are assigned to three days by bounded CP-SAT.
- Every candidate includes arrival and departure anchors, check-in/check-out, two overnight stay nodes, and all selected activities.
- Two nights and one captured stay offer are part of the candidate's ordinary `PlanVersion` truth.
- A complete directed mode matrix is captured before solving; each concrete leg references the selected frozen fact.
- Top-K candidates are persisted as ordinary `CANDIDATE` PlanVersions and are selected through the normal frozen-evidence feasibility gate.
- Protected C4 anchors are preserved with a real departure buffer derived from the frozen final-leg duration.

The solver chooses ordering, assignment, and mode. CityNexus validates cost, opening windows, route feasibility, stay timing, protected commitments, and arrival/departure slack after the candidate exists.
