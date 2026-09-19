# CityNexus V14 Grounded Adaptive Journey Recovery

Date: 2026-09-13 (Asia/Shanghai)

## Outcome

The V14 recovery slice is implemented against the authoritative `D:\moodle\CityNexus` worktree. The flagship path now carries a grounded selected PlanVersion through execution, a sealed provider reality change, incident-time evidence, semantic impact interpretation, deterministic recovery verification, existing delegation policy, acceptance as a child PlanVersion, and the authoritative JourneyTwin/UI/offline surfaces.

The strict V14 Golden uses sealed-real replay evidence. It does not claim live traffic: the configured Valhalla status endpoint was not available in this environment, so the release labels route evidence `SEALED_REAL_REPLAY` and keeps live capability unclaimed. No DeepSeek key was configured during this run; the server-side deterministic impact target was used for the Golden, while the DeepSeek impact contract remains available for configured runs.

## Golden result

- Initial selected mobility synthetic count: `0`.
- Recovery selected mobility synthetic/mock count: `0`.
- Haihe Cruise C4 remained protected.
- DEPARTURE C4 was evaluated and remapped at the activity `END` boundary.
- The accepted recovery is a child `PlanVersion` with lineage to the baseline.
- JourneyTwin, authoritative execution, map/offline snapshot, and the UI all reflect the accepted child truth.
- Browser Golden also reloaded the accepted journey offline and displayed the saved read-only snapshot.

## Safety and evidence boundary

The implementation keeps `baseline_plan_evidence` immutable and records a separate `incident_recovery_evidence` object. Traffic/schedule recovery does not silently reuse baseline route facts as current reality. A live Valhalla claim requires a successful `/status` capability probe. Degraded legacy fallback is retained and explicitly labelled `DEGRADED_BASELINE_REFERENCE`; it cannot satisfy the strict fully grounded Golden.

DeepSeek is used as the semantic layer when configured, but model-only coordinates, prices, opening hours, route durations, weather, or commitment mutations never become authoritative without server-owned evidence and deterministic verification.

## Release evidence

- Focused V14/provider/weather/recovery regression: green; final focused run covered 25 tests after the narrow legacy compatibility correction.
- Broad backend convergence regression: `390 passed, 2 skipped, 2 warnings`.
- Final frontend production build: green (`vite build`, 1,899 modules).
- Playwright session `v14`: compose/execute, sealed weather disruption, recovery proposal, accept child PlanVersion, offline reload, online restore.
- Browser screenshot: [v14-recovery-accepted.png](./v14-recovery-accepted.png).
- Target artifact: `CityNexus-V14-Grounded-Adaptive-Journey-Recovery-20260913.zip`.

