# CityNexus Solver Runtime V1 Status

Date: 2026-09-10

Local Solver Runtime V1 gate: **PASS**.

External freeze status: **PENDING REVIEW**.

The first real OR-Tools increment is wired into `generate_replan()` for Closure and Weather replacement windows between the current execution position and the next durable C4 anchor. CP-SAT solves option presence and start time from pure integer-minute input, verified opening hours, remaining budget, the operation-scoped frozen MobilitySnapshot, Journey horizon, and a fixed C4 safety boundary.

Every materialized solver candidate passes the existing CityNexus deterministic feasibility gate with the same frozen MobilitySnapshot before it can become `PRESENTED`. Rejected solver candidates and Activities are removed. Missing OR-Tools, disabled mode, UNKNOWN, MODEL_INVALID, no assignments, or post-gate rejection retain the deterministic heuristic path with honest fallback provenance.

The default is `CITYNEXUS_SOLVER=deterministic`. `ortools` and `auto` are server-owned modes. OR-Tools remains an optional dependency and is not required for the offline course demo.

No full-day TSP, multiple mutable activity optimization, provider call inside solver/gate, C4 mutation, frontend authority switch, or later product stage was added.
