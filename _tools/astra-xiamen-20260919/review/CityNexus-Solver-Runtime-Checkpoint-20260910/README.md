# CityNexus Solver Runtime V1 Review Checkpoint

This package contains the first real OR-Tools replacement-window runtime after ORT-01 through ORT-20 and all inherited Weather, Provider, and backend-connected Golden gates passed.

Start with `CURRENT_STATUS.md`, `SOLVER_RUNTIME_ARCHITECTURE.md`, `TEST_RESULTS.md`, `BLOCKERS.md`, `contracts/SOLVER_RUNTIME_FREEZE_GATE.md`, and `contracts/ORT_TEST_MATRIX.md`.

Install the optional solver dependency with `pip install -e "./backend[solver,dev]"` when running the real CP-SAT branch. The default `CITYNEXUS_SOLVER=deterministic` remains offline-safe; use `CITYNEXUS_SOLVER=ortools` or `auto` only as a server-owned setting.

The package includes source, tests, fixtures, schema, OpenAPI contracts, static-boundary and validation tools, and inherited frozen-stage documentation. It excludes virtual environments, dependency directories, build output, test results, caches, bytecode, and runtime databases.

This checkpoint stops at Solver Runtime V1 and is awaiting external freeze review.
