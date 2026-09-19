# CityNexus V13.1.1 Final Report

## Scope

This is the narrow V13.1.1 semantic-integrity release. It does not expand
into V14 or redesign solver, inbox, frontend, MCP, provider, or C4 systems.

## Files changed

- `backend/app/operations/v9.py`
- `backend/app/planning/authoritative_v12.py`
- `backend/tests/test_v13_1_1_semantic_integrity.py`
- `reports/product-v13.1.1/FINAL_REPORT.md`

## Implemented behavior

- `ARRIVAL` keeps the existing arrival anchor, destination, and arrival time.
- `DEPARTURE` now writes only the departure anchor with origin and scheduled
  departure time, uses `departure-anchor` by default, and schedules the
  Commitment at `scheduled_departure_at`.
- `MID_TRIP` remains on the existing V13 behavior, including its arrival-time
  Commitment semantics and unchanged Journey anchors.
- `_solve_day_assignment()` now returns the assignment with the optimizer that
  actually produced it. Optional-solver import or solve fallback reports
  `CITYNEXUS_DETERMINISTIC_ASSIGNMENT`; a successful CP-SAT result reports
  `ORTOOLS_CP_SAT`. The actual value is persisted in PlanVersion score
  breakdown, PlanVersion explanation, and the authoritative-compose response.

## Tests

- Focused V13.1.1, V13 integrity, V12 authoritative execution, and V9 trip
  operations: **32 passed, 2 warnings**.
- Broad backend regression: **372 passed, 2 skipped, 2 warnings**.
- Final fresh-extract targeted release gate: **PASS**. The extracted package
  ran the focused semantic-integrity/V13/V12/V9 test set without copying or
  repairing files.

## Release artifact

`CityNexus-V13.1.1-Departure-Solver-Provenance-20260913.zip`

The archive excludes secrets, databases, caches, virtual environments, build
outputs, and nested archives. No real blocker remains for this narrow release.
