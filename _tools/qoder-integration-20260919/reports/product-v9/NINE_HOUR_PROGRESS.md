# CityNexus Real-World Trip Operations V9 — Progress

GOAL_START: `2026-09-12T17:00:38+08:00`  
TARGET_END: `2026-09-13T02:00:38+08:00`  
FINAL_OBSERVATION: `2026-09-12T18:52:11+08:00` after archive verification and fresh-extract replay.

The requested nine-hour budget was treated as an upper bound. The implementation reached the required gate early; the report deliberately records the actual elapsed time rather than claiming nine hours of runtime.

## Baseline

- Existing dirty workspace preserved; no reset, checkout, clean, or automatic commit performed.
- V7 and V8 final archives were preserved.
- Supplied external V9 checker reproduced exactly: `0 passed / 6 failed`.
- V8 focused backend + OpenAPI: `8 passed, 2 warnings`.
- Backend full baseline: `330 passed, 2 skipped, 2 warnings`.
- Frontend production build: `PASS` with the existing large-chunk advisory.
- Frontend Playwright baseline, serialized: `10 passed`.
- `AMAP_WEB_KEY`, `GTFS_RT_URL`, `OTP_BASE_URL`, and `DUFFEL_ACCESS_TOKEN` were not configured at baseline.

## Progress log

| Time | Work | Evidence |
|---|---|---|
| 17:00–17:03 | Read the V9 package instructions, external review, environment analysis, provider research, contracts, checker, and expected output. | Assist package staged at `D:\moodle\_citynexus_v9_assist_20260912`, outside the repository. |
| 17:03–17:06 | Captured Git/test/build/browser baseline and reproduced all supplied failures. | Baseline above; checker initially reported `0 passed / 6 failed`. |
| 17:06–18:06 | Reconciled Stay selection with core PlanVersion, JourneyTwin, concrete JourneyLegs, deterministic post-action gates, generic city fixtures, cost evidence, opening-hours evidence, provider geometry, and autonomy-envelope execution. | `backend/tests/test_v9_real_trip_operations.py`, `backend/tests/test_v8_stay_mobility.py`, and the six-gate checker. |
| 18:06–18:20 | Added Journey Inbox, reservation/Commitment materialization, schedule freshness/service alerts, luggage/check-in sequencing, offline snapshot, location/push seams, edge device endpoints and simulator. | V9 backend tests and OpenAPI parity. |
| 18:20–18:31 | Completed Live Journey mobile/PWA pass, real MapLibre provider geometry, Amap navigation deep link, i18n seam, Evidence drawer, and curated screenshots. | V9 Playwright scenario plus mobile/offline screenshots. |
| 18:31–18:37 | Ran final static checks, deterministic Promptfoo evaluation, MCP boundary tests, model/provider status smoke, and serial full regressions. | Backend `334 passed, 2 skipped`; Playwright `11 passed`; MCP `6 passed`; Promptfoo `13/13`; Ruff/compile/build pass; external checker `6/6`. |
| 18:48–18:52 | Built the single final archive, verified required reports/evidence and exclusion rules, extracted it outside the repository, and replayed backend/frontend checks. | Archive had `7,867` entries, `0` forbidden entries; extracted backend `14 passed`; extracted frontend `npm ci` + build PASS. |

## Test-run integrity note

One intermediate attempt started backend pytest and Playwright concurrently. Both reset the same SQLite fixture and produced unique-key/lock failures; that run is explicitly not counted as evidence. The final runs were serialized and passed in full.

## Runtime labels

- Deterministic/captured/replay paths are labelled as such in `GATE_MATRIX.md` and `PROVIDER_STATUS.md`.
- The bounded DeepSeek smoke returned `FAILED_BLOCKED` with `deterministic-fallback`; its key was loaded only into the child process and was never printed or packaged.
- Hermes MCP V2 is protocol-tested, but an external Hermes CLI/model-backed run is `NOT_RUN_EXTERNAL`.
- Live Amap, GTFS-RT/OTP, and Duffel integrations remain `NOT_CONFIGURED`; captured/replay contracts remain exercised.
