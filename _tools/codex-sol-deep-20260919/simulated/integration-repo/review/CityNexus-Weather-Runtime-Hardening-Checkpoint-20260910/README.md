# CityNexus Weather Runtime Hardening Review Checkpoint

This package contains the server-owned Open-Meteo runtime after WRT-01 through WRT-12, the refresh/scope hardening checks, and adversarial WRH-01 through WRH-06 all passed.

Start with `CURRENT_STATUS.md`, `WEATHER_RUNTIME_ARCHITECTURE.md`, `TEST_RESULTS.md`, `BLOCKERS.md`, and `contracts/WEATHER_RUNTIME_HARDENING_FREEZE_GATE.md`.

The package includes the source, tests, fixtures, schema, OpenAPI contract, verification tools, and solver-stage roadmap needed for external review and fresh-extract reproduction. It excludes virtual environments, dependency directories, build output, test results, caches, bytecode, and runtime databases.

This checkpoint stops at Weather Runtime Hardening. It contains no new OR-Tools implementation.
