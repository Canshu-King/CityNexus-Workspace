# V13.5 Test Results

## Focused implementation checks

- Valhalla/provider foundation, V13.3 Golden compatibility, V13 integrity
  mixed-provenance guard, and web-research tests: **12 passed**.
- Nested DeepSeek source-envelope probe: **2 observations extracted**.
- Fully Grounded Golden API run: **201**, selected plan, synthetic selected
  count **0**.

## Convergence checks

- Backend broad regression, project Python 3.12 plus declared development/
  solver extras and process-only PyYAML for the existing contract test:
  **388 passed, 2 skipped, 4 warnings** in 66.56 seconds.
- Frontend production build: **PASS** (`vite build`, PWA output generated).
- Meaningful browser flow: **PASS**,
  `frontend/e2e/v13-5-fully-grounded.spec.ts` (1 passed).
- Final fresh-extract gate: **PASS**. The release archive was extracted to a
  directory outside `D:\moodle\CityNexus`; the targeted backend runtime proof
  passed from that extraction and forbidden runtime artifacts were absent.

## Environment notes

The default system `python` is 3.10 and cannot import the worktree's existing
`enum.StrEnum` contract. Focused checks used installed Python 3.13; the broad
gate used the project-compatible Python 3.12 environment. No source shim or
new repository dependency was added.
