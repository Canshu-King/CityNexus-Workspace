# CityNexus WP06 Follow-up / WP07 Road-Prep Checkpoint

Date: 2026-09-10

This checkpoint captures the accepted working tree after the supplied
`CityNexus-WP06-WP07-Road-Prep-Deep-Assist-20260909` contract was read and its
prepared patch was applied. It is a review package, not a request to begin a
later work package.

## Scope completed

- Applied `WP06_WP07_ROAD_PREP_20260909.patch` after a clean `git apply --check`.
- Preserved the existing Post-WP04 Foundation, deterministic WP06 core, and
  JourneyTwin v2; no rollback or architecture redesign was performed.
- Completed the WP06 follow-up repair gate: authoritative feasible candidate
  count, verified preference scoring, completed-C4 filtering, generation
  idempotency, deterministic tie ordering, and neutral opportunity scoring.
- Wired a truthful F3 opportunity-window family with exactly one mobility
  estimate per inbound/outbound leg, the configured safety buffer, the next
  upcoming C4 anchor, opening-hours checks, and the same authoritative
  feasibility gate.
- Retained optional Valhalla with MobilitySnapshot freezing and fallback
  provenance. The live smoke remains opt-in only.
- Added server-owned Open-Meteo provider-verified event ingestion; public event
  input cannot forge provider-verified or system-derived evidence.
- Added an optional OR-Tools candidate adapter whose output still passes the
  deterministic verified feasibility boundary. OR-Tools is not mandatory.
- Added optional LiteLLM/DeepSeek wiring behind the existing deterministic
  fallback. No API key or live model is required for the default path.
- Added the contract-first frontend shell and the supplied Playwright golden
  scenario. Backend/domain truth remains authoritative; the shell is offline
  and deterministic.

## STOP gate evidence

- Backend regression: **144 passed, 1 skipped, 2 warnings**.
- Skipped test: opt-in live Valhalla smoke; `CITYNEXUS_LIVE_VALHALLA_URL` was
  unset. No live service was required.
- Ruff check: **PASS**.
- Ruff format check: **PASS** (96 files already formatted after the run).
- Python `compileall -q app tests`: **PASS**.
- OpenAPI: **3.1.0**, formal operations **38**, runtime operations **38**, exact
  match with no missing operations.
- Frontend production build: **PASS** (`vite build`).
- Playwright: **1 passed** (`e2e/golden.spec.ts`).
- No SHA, file hash, archive hash, or hash manifest was computed for this
  checkpoint.

The two warnings are upstream TestClient/AnyIO deprecations already present in
the test environment. WP05/WP06 implementation and the roadmap sequence stop
at this checkpoint pending external GPT review; no WP08 or later work was
started.

