# File and symbol overlap matrix

| File / symbol | Truth v6 | Visual/IA | Prerequisite | Conflict class | Resolution |
|---|---:|---:|---:|---|---|
| `V8Experience.tsx` disruption/budget helpers | yes | yes | no | semantic + structural | Truth helpers win; layout wraps them without reimplementing state |
| `V8Experience.tsx` Live/LiveSecondary | yes | yes | no | behavioral blind spot | Add cursor-derived window (CX-SOL-001) |
| `LiveRecovery.tsx` accepted trigger filtering | yes | yes | no | semantic + structural | Preserve linked-trigger join and decision order |
| `package.json` | yes | no | yes | additive textual overlap | Union scripts; prove with typecheck/build |
| `v8Types.ts` | no | no | yes | prerequisite | Keep integration shape; add fields only from real API contract |
| `v10Execution.ts` | no | no | yes | prerequisite | Keep request/response behavior from group B |
| `main.tsx` | no | no | yes | startup behavior | Keep group B startup fixes |
| `MapPanel.tsx` | no | no | yes | graceful degradation | Keep lazy/empty/error behavior |
| mobility runtime/capture/snapshots | yes | no | no | truth owner | Truth v6 wins; no visual edits here |
| replan endpoints in `main.py` | yes | no | no | truth owner | Preserve allowlist, trigger, C4 and idempotency gates |
| `LocaleContext.tsx` | yes | indirect | no | wording semantics | Preserve activity-vs-trip budget qualifiers |

