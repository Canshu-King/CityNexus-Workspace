# CityNexus V13 Final Report

## Executive result

V13 hardens the V12 authoritative path around server-owned execution state,
immutable provider evidence, deterministic Trip Studio feasibility, active-trip
progress preservation, and commitment-centric recovery. The local flagship
Golden Scenario is green through the domain mutation and offline projections.

The report is deliberately split between what is proven locally and what needs
an external runtime. The current process did not contain DeepSeek/Hermes keys or
a Phoenix endpoint, and the V13 composer Golden uses an explicit synthetic
fixture. Neither fact is hidden behind a green test label.

## Runtime contract

- Runtime label: `V13_LOCAL_REPLAY_AND_SYNTHETIC_AUTONOMOUS_GOLDEN`
- T0: `2026-09-13T03:38:15.3131334+08:00` (Asia/Shanghai)
- Earliest allowed final time: `2026-09-13T11:38:15.3131334+08:00`
- Starting HEAD: `7d22cd0eb7840121ba42a5ba363e1a4c7ca1a7e7`
- Branch: `master`
- Existing dirty worktree changes were preserved; no reset, clean, commit or
  push was performed.

## Delivered implementation

- authoritative predecessor transition graph and terminal/wrong-plan guards;
- immutable, hashed V12/V13 mobility evidence replay in Trip Studio;
- one shared deterministic post-action feasibility gate for preview and accept;
- progress-preserving active Journey edits and truthful leg metrics;
- Journey Inbox mid-trip C4 semantic anchors and commitment binding;
- replay-aware signal ingestion, observation reuse, retryable Guardian runs and
  worker/database stability improvements;
- offline/service-worker path convergence and asynchronous operations streaming;
- preserved V4–V11 compatibility only where it cannot weaken the authoritative
  V12/V13 contract.

## Required gate results

- P0 integrity gate: **PROVEN for the local authoritative replay/synthetic
  contract**; see `P0_INTEGRITY_GATE.md`.
- Meaningful external findings: **6 reproduced; 6 addressed in the supported
  local path**. Finding F remains explicitly scoped to a local single-device
  offline flow, not multi-device conflict resolution.
- Backend: **369 passed, 2 skipped, 2 warnings** on the backend-scoped full
  regression.
- Frontend/build/E2E: production build PASS, Storybook build PASS, full
  Playwright **16 passed**, including mobile/accessibility/offline coverage.
- Golden recovery: **PASS locally** through replay signal, Event, Guardian,
  policy, deterministic mutation, JourneyTwin and offline snapshot.
- Mid-trip C4: **PROVEN** through Journey Inbox import/confirm, authoritative
  compose, selected Activity binding and recovery protection.
- Provider evidence: **captured Tianjin replay proven; V13 composer live matrix
  partial because the deterministic Golden uses labelled synthetic facts**.

## External/runtime limitations

DeepSeek, Hermes, Phoenix external export and literal Promptfoo/model-backed
evaluation were not configured in this process. The final gate matrix records
each as `EXTERNAL / NOT CONFIGURED` or `PARTIAL`; the gateway does not grant
authority merely because a model is present. Local MCP, OpenAPI, static solver
boundary, local adversarial adapter (`13/13`) and secret scan are green.

## Final artifact

The curated archive is
`D:\moodle\CityNexus\CityNexus-V13-Authoritative-Integrity-Commitment-Recovery-20260913.zip`.
It contains 318 curated entries and excludes secrets, databases, caches,
virtual environments, build outputs, browser raw dumps and nested historical
archives. The final archive was fresh-extracted and validated at
`D:\moodle\_v13_fresh_extract_20260913_final`; the extracted source also passed
Python compilation. The archive and its fresh-extract validation are therefore
**PROVEN** deliverables, not a pending final-window task.

## Final convergence evidence

The hard gate was satisfied at `2026-09-13T11:53:07.1833493+08:00`; final
regression finished at `2026-09-13T11:59:20.8892854+08:00`. That is
`8h 21m 5.576s` of wall-clock runtime from the exact T0 above. The final
post-gate results are recorded in `FINAL_REGRESSION.md`: backend `369 passed,
2 skipped`, focused V13/V5/V6 `25 passed`, full Playwright `16 passed`,
production and Storybook builds passed, and the package-independent contract,
secret, compile, and sealed-replay checks passed.

The campaign addressed six supplied external findings and four additional
post-green runtime races (duplicate service-worker ownership, the sole-worker
offline module gap, delayed Guardian truth hydration, and process-global worker
drain/reset overlap). This is a count of reproduced-and-fixed findings, not a
claim that external model/provider services were live.
