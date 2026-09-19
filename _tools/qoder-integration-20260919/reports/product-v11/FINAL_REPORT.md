# CityNexus V11 Final Report

## Outcome

V11 delivered the RealAgent → provider-backed Compose → Gateway/Policy →
execution UI product path. The flagship live Agent run used DeepSeek V4.1 Flash
tool selection, persisted an AgentRun/tool trace, and executed an envelope-safe
replan through the CityNexus domain. Prior V5/V6/V7/V8/V9/V10 artifacts remain
in the workspace and were not reset.

## Validation

- P0 checker: 8/8.
- Scoped backend regression: 344 passed, 2 skipped, 2 warnings.
- Frontend build: passed.
- Storybook build: passed.
- Frontend Playwright: 14 passed, 1 failed (legacy V6 reload assertion).
- Live DeepSeek tool probe: HTTP 200, function call selected.
- Live CityNexus Agent mutation: passed with `ALLOW_AUTO` and accepted plan mutation.
- Secrets were process-only and excluded from deliverables.
- Fresh extract contains 405 files; package hygiene found no dependency trees,
  build caches, runtime databases, nested archives, or temporary env files.

## Honest external boundaries

Valhalla/GTFS/OTP, SearXNG, Hermes, Phoenix, and model-backed visual critique
were not configured as live external services in this workspace. Their adapter
or contract surfaces remain explicit and are not called PASS merely because a
replay exists. The one V6 reload UI follow-up is recorded in the gate matrix.

## Deliverable

`CityNexus-V11-RealAgent-Compose-Execution-UI-Final-20260913.zip` is assembled
from current product source, runtime contracts, tests, reports, and replay data;
secrets, environments, dependencies, build caches, runtime databases, nested
archives, and historical review trees are excluded.
