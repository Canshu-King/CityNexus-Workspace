# Integration change map

Snapshot: 2026-09-19 14:12 +08:00. Verified against read-only commit `1a8462dbc0108585266f637350202f9587ca532c`.

| Layer | Commits/files | Verified behavior | Reconciliation note |
| --- | --- | --- | --- |
| Authoritative freeze | `380e6ff` from main `7d22cd0` plus working tree | 6,542-file integration baseline | Treat as historical base; do not merge the dirty main worktree now |
| Truth/backend | `b12f24f`; mobility runtime/capture/Valhalla, main, planner, replanning, replay | Exact/fail-closed provenance, candidate isolation, physical identity, hard-mobility allowlist | Highest semantic priority; frontend must consume it without inventing fallback truth |
| Frontend truth surfaces | `b12f24f`; `V8Experience`, `LiveRecovery`, budget/disruption helpers | ACK vs resolution and budget evidence rendered | Preserve API semantics when applying IA work |
| Frontend visual/IA | `e330ac2`; `V8Experience`, `LiveRecovery`, design tokens, four visual gates | Today/Live structure, motion and dark semantics | Product decisions remain for duplicated language, CTA overload, Live action order and dock overlap |
| Frontend prerequisite type/behavior | `a2124c0`; API types, map GeoJSON, planning/studio/notifications, `main.tsx` | Broad typecheck restored; 11-file +35/-17 reconcile | Keep surgical edits; do not wholesale replace CRLF/current files |
| Test/evidence | `cfb2b4a`; real-seed setup, two-theme contrast gate, Playwright config | Full suite improved from 30/15 to 34/12; light AA defects exposed and fixed | Twelve remaining failures are legacy/product-contract drift, not all seed failures |
| Evidence/tooling | `1a8462d`; integration report, capture tool, 32 screenshots | Readable Today/Live matrix and issue list | Evidence commit, not proof of phone/Valhalla release readiness |
| Environment-only | Valhalla URL, ports, device, TLS, AI keys | Not configured/proven by integration commit | Owner gate; never commit secrets or equate desktop seed with live provider/device |

## Risky overlap map

| File/symbol | Competing behavior | Recommended winner | Rule | Gates |
| --- | --- | --- | --- | --- |
| `frontend/src/app/V8Experience.tsx` | truth ACK/budget rendering vs Apple Today/Live IA | Both | Reconcile semantically; server truth/state linkage wins, then presentation order | qoder ACK/budget, full seeded E2E, screenshots |
| `frontend/src/features/execution/LiveRecovery.tsx` | proposal truth and resolution vs presentation/motion | Both | Never derive resolved from ACK alone; motion may follow state but not create it | ACK-resolution, material diff, accept idempotency |
| `frontend/src/main.tsx` | legacy golden flow vs prerequisite type fix | Current integrated surgical patch | Keep session spread fix and lazy map; do not restore obsolete `/` assumptions | typecheck:all, golden replacement contract |
| `frontend/src/components/v8/MapPanel.tsx` | GeoJSON typing vs dynamic MapLibre | Current integrated | Preserve dynamic import and valid FeatureCollection typing | build, no-map startup, map failure |
| `frontend/src/design-tokens.css` | Apple accent vs WCAG AA | `--cn-accent-text` for small text | Separate text and solid/action colors | axe, light+dark contrast |
| `frontend/playwright.config.ts` | shared real seed vs test isolation | Setup project with explicit state file | Seed only through public APIs; no DB/route fulfillment | setup log, full suite |
| `backend/app/main.py` | legacy endpoint behavior vs hard live truth | v6 truth behavior | No mock hard fallback when live is configured | live-replan focused tests, 422 unavailable |
| `data/replay/tianjin...json` | replay label vs explicit fact quality | Explicit persisted quality | Replay status never inferred from broad labels | provenance exact gate |

## State at snapshot

- Integration HEAD is clean but detached at `1a8462d`.
- Main remains `eac/v19.2.2-realphone-codegate` at `7d22cd0` with its historical untracked working tree.
- No merge, deployment, Valhalla enablement or Xiaomi trial is inferred.
