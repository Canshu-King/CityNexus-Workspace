# Solver strategy

## Primary path: OR-Tools

Use OR-Tools from Python after the deterministic WP06 baseline is already correct.

CityNexus owns:
- hard constraints;
- commitment protection policy;
- scoring semantics;
- provider facts;
- acceptance validation.

OR-Tools owns only the combinatorial search/optimization problem that CityNexus gives it.

## Timefold

Retain as an optional comparative/advanced solver experiment, not a core dependency. Current Timefold Solver is Java/Kotlin-oriented; introducing a second runtime/service before OR-Tools proves value is not justified.

A future `PlannerAdapter` may expose:

```text
DeterministicHeuristicPlanner
ORToolsPlanner
TimefoldPlanner (optional service)
```

All must return the same CityNexus candidate contract and still pass the authoritative feasibility gate.
