# Focused execution evidence

Snapshot under test: disposable clone at `1de4e0c569349d7eee4bc22995cc49c487e3279e`.

## Backend focused gate

Command selected eight hypothesis-driven files covering mobility truth, physical identity, hard fallback, live replans, idempotent acceptance, material diffs, weather degradation and provider adapters.

Result: **81 passed, 1 deprecation warning, 18.75 s**.

## Stateful model

`python tests/stateful_recovery_audit.py --sequences 5000 --steps 80`

Result: **PASS — 400,000 transitions, 12 invariants, seed 20260919**.

## Candidate frontend

- `tsc -p frontend/tsconfig.typecheck.json --noEmit`: PASS
- `vite build`: PASS; main 1,127.01 kB / 334.05 kB gzip, MapLibre 1,053.38 kB / 284.76 kB gzip
- `playwright test e2e/codex-live-current-activity.spec.ts --project=chromium --no-deps`: **1 passed (2.7 s)**

Two exploratory versions of the browser assertion waited too long for secondary map text while the deliberately minimal mock later entered the app error boundary. The final regression is intentionally scoped to the contract defect: current and next visible activities. Product typecheck/build remained green throughout.

## Protected source observation

At final read-only status inspection, the active integration tree had uncommitted modifications in `frontend/src/app/V8Experience.tsx` and `frontend/src/design-tokens.css`, consistent with the concurrently active Qoder run. Codex did not write, reset, commit, clean or merge that tree. All candidate changes exist only in the disposable clone and output package.

