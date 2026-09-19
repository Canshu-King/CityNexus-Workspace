# CityNexus Weather Runtime Review Checkpoint

This package contains the server-owned Open-Meteo runtime path after WRT-01..WRT-12 and the additional trigger/scope hardening checks passed.

Read `CURRENT_STATUS.md`, `WEATHER_RUNTIME_ARCHITECTURE.md`, `TEST_RESULTS.md`, and `contracts/WEATHER_RUNTIME_FREEZE_GATE.md` first.

The refresh operation is `POST /api/v1/journeys/{journey_id}/weather/refresh`. It accepts no request body. The server selects eligible Places, calls Open-Meteo, freezes UTC evidence, performs deterministic attribution, and creates or reuses trusted Events.

The package excludes virtual environments, dependency directories, build output, test reports, caches, bytecode, and runtime database files.
