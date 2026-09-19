# CityNexus Sol V2 Narrow Closeout Report

## VERIFICATION RESULT

`COMPLETE` for the reference single-worker deployment scope.

The disposable candidate is commit `776be4e` on top of accepted candidate `c19daa5`. No authoritative, Qoder, or integration worktree was modified.

Implemented closeout changes:

- C4 capture remap now ranks exact semantic identifiers ahead of place/service overlap, requires exactly one valid time-bound match, and fails closed for zero or multiple matches.
- Live uses the backend's first-non-terminal rule for a null cursor. A present-but-unknown cursor still yields no Now, Next, or leg.
- Journey write serialization is explicitly marked `PROCESS_LOCAL_ONLY`; the lock registry uses weak values so inactive Journey keys do not grow without bound.
- Focused regressions cover unique/no-match/semantic-conflict/ambiguity C4 cases and all six requested Live cursor cases.

Final gates:

| Gate | Result |
|---|---|
| Full backend | 832 passed, 15 skipped, 0 failed |
| Qoder truth-contract focus | 65 passed, 0 failed |
| Real API state machine | 1 passed, 60 examples × 30 steps |
| Concurrency schedules | 5/5 clean, 0 dangling commitments |
| Projection oracle | 7 cases, 0 divergence |
| Live browser projection | 6/6 passed |
| Mutation campaign | 17/17 killed, 0 survivors, 0 errors |
| Frontend production build | passed |
| Repository TypeScript typecheck | 5 pre-existing errors, exact baseline/candidate match |

The unchanged TypeScript errors are three `ProductErrorBoundary` React class typing errors, one `SortableActivityList` JSX `key` typing error, and one `V12ExecutionStates` story JSX `key` typing error. The same five diagnostics occur at baseline `c19daa5`; no closeout-delta type error exists.

## MERGE RECOMMENDATION

Do not merge or cherry-pick `c19daa5` or `776be4e` blindly. Selectively port the narrow behavior after reconciling with the current integration line described in `CONVERGENCE_MATRIX.md`.

The in-process RLock is acceptable only while the reference deployment remains one worker. Before any multi-worker/process deployment, replace it with database row locking, an advisory lock, or equivalent distributed serialization covering the complete read/validate/write transaction for replan acceptance and booking/payment capture.

The current line already contains stronger Qoder mobility, physical-identity, and authoritative-E2E contracts. Those contracts should remain authoritative during integration.

## Evidence layout

- `raw/final/`: only final authoritative logs and machine-readable results.
- `raw/intermediate/`: superseded environment-diagnostic evidence only.
- `candidate_patch/`: one review patch for commit `776be4e`.
- `focused_tests/` and `replay_cases/`: executable regressions and harnesses.

No merge was performed.
