# CityNexus V12 Final Report

## Outcome

The V12 completion gate is **PASS for the local product/runtime path**: one authoritative multi-day Journey can be composed, selected, edited, executed, and autonomously recovered while PlanVersion, JourneyTwin, the active-plan route/map data, Mobile-facing execution state, Offline snapshot, and PIC Edge all use the same durable provider evidence and live execution truth.

The implementation preserves V11 and extends it with a real authoritative V12 path rather than replacing the existing Agent architecture.

## Delivered product path

1. CP-SAT composition creates bounded Top-K complete plans for six POIs across three days/two nights with Stay, arrival/departure, and protected reservation inputs.
2. Provider mobility facts are normalized into durable PlanVersion evidence, including a complete directed mode matrix and selected leg facts.
3. Selection replays the candidate's evidence and deterministic gate; it does not silently recapture a new provider world.
4. Execution records `NOT_STARTED → EN_ROUTE → ARRIVED → IN_PROGRESS → COMPLETED/SKIPPED`, actual timestamps, and outcome events.
5. Offline and Edge projections read the same execution snapshot; JourneyTwin exposes the same NOW/NEXT state.
6. Trip Studio keeps reorder local until preview, evaluates the same frozen evidence and protected anchors, and accepts into a new `MANUAL` PlanVersion.
7. Guardian/Gateway recovery can return `ALLOW_AUTO` for an ordinary reversible activity inside the user's Autonomy Envelope, with deterministic post-action hard-constraint and business-fact verification.
8. The demo/runtime reset boundary stops the process-global Guardian worker before reseeding, keeping Journey-scoped autonomous enrollment aligned with the authoritative Journey under repeated local/E2E resets.

## Validation

| Gate | Result |
| --- | --- |
| Full backend regression | 347 passed, 2 skipped on fresh external SQLite |
| V12 flagship backend tests | 3/3 passed; included autonomous envelope recovery |
| V8/V10 compatibility focus | 6/6 passed in the scoped run; combined V12 focus 9/9 |
| P0 implementation gate | 9/9 passed |
| OpenAPI parity | 4/4 passed |
| Python compile | PASS |
| Frontend build | PASS |
| Storybook build | PASS |
| Playwright desktop/mobile/accessibility suite | 15/15 passed |
| Map resize probe | PASS at desktop and 390px mobile viewport |
| Secret/package hygiene | PASS at final staging scan |

## Honest limitations

- The current environment has no configured SearXNG or Phoenix endpoint; the sourceful web and tracing contracts return explicit `NOT_CONFIGURED` rather than fabricating live coverage.
- 21st.dev was not a callable Codex capability in this runtime. Existing mature libraries were used and recorded in `docs/frontend/THIRD_PARTY_ADOPTION_V12.md`; no unverified third-party source was copied.
- The redacted DeepSeek evidence records a real model-generated V12 proposal and a Gateway `ALLOW_AUTO` execution continuation. In that particular bridge run the model stopped after presenting the proposal, so the direct Gateway continuation is marked separately from a pure model-issued `accept_replan` step. Existing V11 live tool-loop coverage remains intact.
- The nine-hour package budget was not claimed as elapsed time because the prior turn did not persist a reliable start timestamp. This report is labeled an interactive engineering checkpoint.

## Security and packaging

`TEMP_DEEPSEEK.env` was loaded only into a child process during live-provider work. Keys, databases, caches, virtual environments, frontend build output, raw browser logs, and historical archives are excluded from the final V12 ZIP. The archive contains only curated product/runtime files and reports.
