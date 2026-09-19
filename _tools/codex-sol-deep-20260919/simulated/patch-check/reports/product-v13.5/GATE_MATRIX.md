# V13.5 Gate Matrix

| Gate | Result | Evidence |
|---|---|---|
| Required package guidance read | PASS | `README_FIRST.md` and `CODEX_V13_5_TASK_PROMPT.md` read from the V13.5 road-prep package |
| One-time mixed-grounding reproduction | PASS | Captured replay reproduced 54 synthetic matrix facts and 2 selected synthetic legs; both anchors collapsed to `journey-anchor` before repair |
| Journey structural provider identity | PASS | `anchor:arrival` and `anchor:departure` are distinct sealed nodes and coordinate-checked |
| Provider-backed mobility modes | PASS | New sealed Tianjin snapshot contains 64 WALK and 64 AUTO matrix cells |
| Journey-specific matrix | PASS | 8 structural/provider nodes; directed matrix is captured for this Journey shape, not a city centroid |
| Route/cost provenance split | PASS | `route_provenance=CAPTURED_REPLAY`, `route_provider=valhalla`, `cost_provenance=CITYNEXUS_COST_ESTIMATE` |
| DeepSeek source envelope | PASS | Nested `action.sources` and URL-citation annotations extracted; no model-only promotion |
| DeepSeek live canary | NOT CONFIGURED | No `CITYNEXUS_AI_API_KEY` or `DEEPSEEK_API_KEY` in the process environment |
| Deterministic candidate gate | PASS | Candidate coordinates, opening hours, and cost remain server/provider facts |
| Fully Grounded Golden | PASS | `runtime_label=FULLY_GROUNDED_JOURNEY`; selected synthetic count `0` |
| Authoritative Compose/PlanVersion | PASS | Selected PlanVersion contains frozen mobility evidence and provider node identities |
| Existing V13 regression | PASS | Focused V13.3/V13 integrity/provider set: 12 passed |
| Broad backend convergence | PASS | 388 passed, 2 skipped, 4 warnings under the project Python 3.12 environment |
| Frontend production build | PASS | `npm run build` |
| Browser product flow | PASS | Playwright V13.5 City Discovery flow: 1 passed |
| Fresh-extract release gate | PASS | Final archive extracted outside the worktree and targeted runtime gate executed there |
