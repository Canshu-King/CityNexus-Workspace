# CityNexus Overnight Execution Report

Date: 2026-09-10  (Asia/Shanghai)
Workspace: `D:\moodle\CityNexus`

## 1. Starting state detected

The first live inspection of this continuation found branch `master` at its
pre-existing HEAD (the commit identifier is intentionally not recorded). The working tree was intentionally
dirty: `.gitignore` was modified and the CityNexus application, contracts,
fixtures, prior review packages, incoming assist packages, Visio renderer
artifacts, and tests were untracked. The short status view contained 31
top-level entries; no reset, checkout, commit, or rollback was performed.
The process check found no active CityNexus pytest/build command. Unrelated
desktop Node/Python processes were left untouched.

## 2. Work already complete before this continuation

No duplicate implementation was started for these accepted foundations:

- WP00-WP03 baseline implementation and its accepted checkpoint;
- WP04 plus the WP04A-0 commitment/location/currency bridge;
- Post-WP04 integration foundation and provider ports;
- deterministic WP06 planning and JourneyTwin v2;
- WP06 lifecycle/idempotency, provenance, and MobilitySnapshot hardening;
- the supplied WP06→WP07 road-prep patch and its initial regression suite.

## 3. Road-Prep phases completed and verified

### WP06 follow-up and F3

- Feasible candidates, rather than raw specs, satisfy `candidate_count`.
- Persisted Traveler interest preferences drive verified `preference_fit`.
- Opportunity value remains neutral until evidence exists.
- Past/completed C4 commitments are excluded from `upcoming_commitments`.
- Replan generation supports replay/conflict semantics for `Idempotency-Key`.
- Equal-score ordering is deterministic and prefers lower disruption before
  preserving generation order.
- Every persisted candidate now carries a verified-evidence bundle covering
  generation rank, feasibility, commitments, stability, budget, mobility,
  time/slack, preference, opportunity, utility, and reason codes.
- F3 is a real `OpportunityWindow` family using current time, the next C4
  anchor, inbound/outbound travel, opening hours, budget, and a 15-minute
  safety buffer before the full feasibility gate.

### Valhalla and MobilitySnapshot

The injectable Valhalla HTTP adapter now validates route/matrix shapes,
non-negative finite durations, and provider failures behind a controlled
error. Captured facts are frozen into `MobilitySnapshot` before any
deterministic gate; fallback facts retain degraded/provider provenance.

### Open-Meteo

The Open-Meteo adapter validates response arrays, timestamps, probability
ranges, and weather codes. Frozen risks feed a server-only
`PROVIDER_VERIFIED` Event. A small internal outage/recovery service records a
`SYSTEM_DERIVED` degradation event and resolves it on provider recovery, so
JourneyTwin returns from `DEGRADED` to `READY` without client-controlled state
mutation.

### OR-Tools and LiteLLM/DeepSeek

OR-Tools remains an optional candidate generator; its output is passed through
the common verified ranking/feasibility boundary. LiteLLM/DeepSeek remains an
optional explanation provider receiving structured verified facts only, with a
deterministic fallback for unavailable, blank, malformed, or failing results.

### Frontend and Playwright

The contract-first React/Vite shell now exposes the Journey Mode vertical:
timeline, current/next activity, budget, commitment buffer, protected
upcoming commitments, feasibility envelope, provider status, map/event/C4
markers, old/new route evidence, candidate families, score/evidence/deltas,
and accept/reject controls. It stays offline and leaves domain truth in the
backend. The Playwright golden scenario covers simulator closure, protected
River Cruise, replan evidence, acceptance, and reload persistence.

## 4. Additional hardening introduced in this continuation

- Added internal Open-Meteo provider degradation and recovery functions.
- Added regression coverage for provider recovery and `JourneyTwin READY`.
- Added controlled Valhalla timeout/malformed route and matrix checks.
- Added controlled Open-Meteo timeout/malformed hourly checks.
- Added blank/malformed AI provider fallback checks.
- Added F3 closed/unaffordable candidate checks.
- Added lower-disruption tie ordering to the API proposal rank.
- Expanded frontend selectors and assertions for the complete Journey Mode
  evidence surface.
- Added conservative requirement status traceability in
  `docs/implementation/wp06-wp07-status-addendum.csv`.

## 5. Test inventory

The review package retains the prior tests and the Road-Prep additions:

- `backend/tests/test_wp06_followup_assist.py` — candidate count,
  preferences, idempotency, completed C4, neutral opportunity, and integrated
  F3 evidence;
- `backend/tests/test_wp07_foundation_assist.py` — F3 fit/failure cases,
  weather snapshot/ingestion, provider recovery, verified ranking, and AI
  mutation policy;
- `backend/tests/test_postgate_provider_foundation.py` — Valhalla snapshot and
  adapter behavior, controlled provider failures, and AI fallback;
- `backend/tests/test_foundation_http_adapters.py` — Open-Meteo parser/risk
  behavior and controlled provider failures;
- `frontend/e2e/golden.spec.ts` — expanded Journey Mode golden scenario.

## 6. Final validation

- Backend: **149 passed, 1 skipped, 2 warnings**.
- Optional skip: live Valhalla smoke because
  `CITYNEXUS_LIVE_VALHALLA_URL` was not configured.
- Ruff check and format check: **PASS**; 96 Python files formatted.
- Python compileall (`app tests`): **PASS**.
- OpenAPI: **3.1.0**, exact formal/runtime operation match **38/38**.
- Frontend Vite build: **PASS**.
- Playwright: **1 passed**.
- Packaged snapshot replay: recorded in `TEST_RESULTS.txt` after archive
  assembly.

## 7. Provider and dependency record

No live provider smoke test completed. Valhalla, Open-Meteo, OR-Tools, and
DeepSeek/LiteLLM remain on mocked, frozen, or deterministic fallback paths.
The frontend dependency set (React, Vite, MapLibre GL JS, Turf, XState,
TypeScript, and Playwright) was installed and locked by
`frontend/package-lock.json`; the Playwright Chromium binary was available to
run the local E2E test. `ortools`, `litellm`, and `routingpy` were not
installed, preserving their optional boundary.

## 8. Requirement-status shifts

The conservative status changes are recorded in
`docs/implementation/wp06-wp07-status-addendum.csv`. Only behavior backed by
the current code and tests is marked `IMPLEMENTED`; provider monitoring,
full AI structured-output validation, broad requirement coverage, and
production asset scanning remain `PARTIAL` or `SIMULATED`.

## 9. Recommendation

Use this package for independent GPT review first. After acceptance, the next
cycle should wire the frontend to the existing backend contracts and decide
whether to enable one optional provider in a separately controlled environment;
do not make external services mandatory for the deterministic gate.
