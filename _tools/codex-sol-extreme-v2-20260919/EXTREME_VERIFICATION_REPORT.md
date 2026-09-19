# CityNexus Sol Extreme Verification v2

Baseline: `0fa1f6cba391ecbc177d8d1dcf72f422033b61b5` (read-only source snapshot).  
Disposable candidate: `c19daa54ba046a92c4638aea8c1c1c69b67724b8`.

## Verdict by track

- **I — REAL API STATEFUL FUZZING: complete.** Hypothesis RuleBasedStateMachine drove up to 1,800 real API/persistence transitions (60 examples × 30 steps), plus six minimized API projection/acceptance regressions. State-machine gate: 1 passed in 37.33s. Focused real API + taint baseline: 17 passed.
- **J — TARGETED MUTATION TESTING: complete.** 15/15 catastrophic mutants killed; no survivor or execution error remains. Exact diffs and killing output are machine-readable.
- **K — CONCURRENCY / RACE AUDIT: complete.** Three real races reproduced and minimized. Candidate passed five consecutive runs of all five schedules with zero invariant violations.
- **L — DIFFERENTIAL PROJECTION ORACLE: complete.** Five generated persisted fixtures, zero backend projection divergences; four focused browser cases passed.
- **M — MOBILITY TRUTH TAINT PROOF: complete.** Static graph plus dynamic allowlist/failure tests prove weak, synthetic, unknown and mock fallback facts cannot enter hard feasibility.

## Verified findings

Four verified defects are recorded in `findings.json`: stale-cursor fabrication, idempotency accept race, competing accepts producing multiple active plans, and booking-capture/replan dangling C4 identity. A single isolated candidate patch contains the fixes and focused frontend regression. Backend regression harnesses are in `tests/`.

## Evidence summary

- Focused final regressions: 36 passed, 21 deselected.
- Browser Live projection: 4 passed.
- Projection oracle: 5 cases, 0 divergences.
- Mutation score: 15/15 killed.
- Candidate concurrency: 5 complete reruns, 0 defects.
- Repository-wide TypeScript gate: blocked by four pre-existing unrelated typing errors in `ProductErrorBoundary.tsx`, `SortableActivityList.tsx`, and `V12ExecutionStates.stories.tsx`; recorded in `raw/frontend_typecheck.log`. The changed Live surface compiles under Vite and passes its browser gate.

## Candidate limitation

The Journey serialization guard is process-local and is suitable for the reference single-worker SQLite deployment exercised here. Before multi-worker production use, replace/supplement it with a database row/advisory lock and rerun the same race schedules across processes.

CODEX_SOL_EXTREME_VERIFICATION_COMPLETE
