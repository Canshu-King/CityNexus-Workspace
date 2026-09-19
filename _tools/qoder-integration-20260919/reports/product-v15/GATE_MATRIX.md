# V15 Gate Matrix

| Gate | Result | Evidence |
|---|---|---|
| Package guidance read in order | PASS | `README_FIRST.md`, `CODEX_V15_OVERNIGHT_TASK_PROMPT.md`, policy/map/acceptance docs |
| Initial repository baseline | PASS | One `git status --short`; dirty worktree preserved |
| Existing focused baseline | PASS | 9 tests passed |
| Explicit semantic intents | PASS | `tests/test_v15_copilot.py` matrix |
| DeepSeek structured interpretation path | PASS | Responses reasoning/message envelope probed with a transient process key; reasoning is excluded from schema text and the final fallback is also verified |
| Ordinary text does not fabricate Events | PASS | Preference, explanation, discovery, and hypothetical API tests |
| Current disruption Event path | PASS | Only `DISRUPTION_REPORT` creates `user-copilot` / `USER_REPORTED` Event |
| Read-only What-If invariants | PASS | No Event or JourneyTwin row change in focused API test |
| V14 recovery reference | PASS | `test_v14_grounded_adaptive_recovery.py` passed in convergence set |
| Broad backend regression | PASS | `uv run pytest -q`: 400 passed, 2 skipped, 2 warnings in 39.62s |
| Frontend production build | PASS | `npm run build` / Vite; existing chunk-size warning only |
| Real-user browser scenarios | PASS | Tonglu, Xiapu, Tianjin, and Beijing journeys; budgets, late starts, hypothetical and current disruptions |
| Generic-city browser flow | PASS | Fuzhou/Xiapu/Beijing setup → City Discovery → Copilot; honest no-plan/provider evidence |
| Sealed Tianjin browser What-If | PASS | Stay selection → AI desk → What-If card with currency, feasibility, simulation-only and protected state |
| No-authoritative-plan guidance | PASS | Beijing What-If explicitly directs the traveler to select a provider-backed PlanVersion |
| Secrets in source/artifact | PASS | No key added; release staging excludes env/key files |
| Fresh-extract release gate | PASS | Final ZIP extraction + backend targeted gate: 12 passed, 2 warnings; required `data/mock` fixtures included |
