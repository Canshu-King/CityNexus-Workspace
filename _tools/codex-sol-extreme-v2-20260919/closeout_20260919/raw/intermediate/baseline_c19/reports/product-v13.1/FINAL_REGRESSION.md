# V13.1 Final Regression

## Main worktree evidence

| Surface | Result | Classification |
| --- | --- | --- |
| Focused V13.1 scope | `37 passed, 2 warnings` in `18.09s` | **PROVEN ONLY IN MAIN WORKTREE** |
| Backend full suite | `369 passed, 2 skipped, 2 warnings` in `48.27s` | **PROVEN ONLY IN MAIN WORKTREE** |
| Full Playwright | `16 passed` in `38.5s` | **PROVEN ONLY IN MAIN WORKTREE** |
| Frontend production build | Vite 7.3.6, 1,897 modules, PASS | **PROVEN ONLY IN MAIN WORKTREE** |
| Storybook build | 1,974 modules, PASS | **PROVEN ONLY IN MAIN WORKTREE** |
| OpenAPI parity | 119 formal / 119 runtime; missing 0 / extra 0 | **PROVEN ONLY IN MAIN WORKTREE** |
| Agent MCP | `6 passed` in `1.99s` | **PROVEN ONLY IN MAIN WORKTREE** |
| Solver boundary | 4 modules checked, PASS | **PROVEN ONLY IN MAIN WORKTREE** |
| Python compile / diff check | PASS / PASS | **PROVEN ONLY IN MAIN WORKTREE** |

The repository-wide Ruff check is not a release gate for this iteration: it
reports pre-existing formatting/import findings in the V13 worktree. The
functional regression and compile/diff gates are green; no unrelated Ruff
cleanup was included in V13.1.

## V13 preservation

The regression retains server-owned execution transitions, frozen-evidence
integrity, deterministic Trip Studio preview/accept, active-trip continuity,
mid-trip C4 protection, JourneyTwin/offline convergence, and the delegated
authorization boundary.

## Fresh-extract result

| Surface | Result | Classification |
| --- | --- | --- |
| Extracted layout | root catalog present; `backend/data` absent | **PROVEN FROM FRESH EXTRACT** |
| Fresh focused backend scope | `73 passed, 2 warnings` in `16.91s` | **PROVEN FROM FRESH EXTRACT** |
| Fresh backend full suite | `369 passed, 2 skipped, 2 warnings` in `37.46s` | **PROVEN FROM FRESH EXTRACT** |
| Fresh frontend dependency install | `npm ci` added 708 packages in `8s` | **PROVEN FROM FRESH EXTRACT** |
| Fresh production frontend build | Vite 7.3.6, 1,897 modules, PASS in `4.74s` | **PROVEN FROM FRESH EXTRACT** |
| Fresh full Playwright | `16 passed` in `36.5s` | **PROVEN FROM FRESH EXTRACT** |
| Fresh archive exclusions | forbidden secrets/data/cache/build/nested ZIP scan clean | **PROVEN FROM FRESH EXTRACT** |

The fresh-extract gate is green. The exact commands and environment boundary
are documented in `FRESH_EXTRACT_RUNTIME_GATE.md`.
