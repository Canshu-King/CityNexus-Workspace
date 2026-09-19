# CityNexus Proactive Journey Guardian V4 — Final Report

Date: 2026-09-11

## Product result

The Proactive Journey Guardian flagship is complete and regression-clean. The milestone is no longer a chat-only replan demo: a user can persist one standing mission and autonomy envelope, after which server-owned weather and traffic events can trigger a proactive scan and one auditable recovery run without another user message.

The execution split follows the intended product architecture:

- DeepSeek can compile ambiguous intent and select semantic impact hypotheses when credentials exist.
- Hermes has a primary runtime adapter and can use the complete allowlisted tool surface when configured.
- OR-Tools CP-SAT V2 performs precise whole-horizon keep/replace/drop and schedule optimization from frozen mobility facts.
- CityNexus validates ownership, activity lifecycle, budgets, commitments, feasibility, and provider facts.
- Delegation Policy plus the standing Mission envelope determines `ALLOW_AUTO`, confirmation, step-up, or denial.

No model judgment is treated as a database fact. Conversely, ordinary reversible activity recovery is not forced into confirmation merely because semantic interpretation came from a model; deterministic post-materialization feasibility and the delegation envelope remain the action boundary.

## Flagship flow verified

1. A Journey is planned, booked, started, and advanced to the disruption point.
2. The user activates a standing mission protecting cruise and dinner, preferring indoor/low-walking options, permitting +¥50, and allowing bounded autonomous execution.
3. Weather and traffic events are persisted for two journey activities without a new chat command.
4. Guardian observes both events and records `RECOVERY_REQUIRED`.
5. One normalized AgentRun inspects the Twin, requests a CP-SAT V2 replan, and invokes acceptance through the Gateway.
6. The selected proposal passes deterministic feasibility and policy checks.
7. Protected activities and the durable C4 commitment remain intact.
8. PlanVersion and JourneyTwin advance atomically.
9. The UI renders the five provenance layers, persisted trace, and old/new map routes.
10. Reload restores the standing mission, Guardian run, active plan, trace, and map evidence.
11. A duplicate scan returns the original run rather than creating noisy duplicate plans.

## External findings

All three supplied findings were independently reproduced before implementation and now pass:

- V4-01: general Chinese cardinal parsing replaces the Arabic-only money parser.
- V4-02: activity authority is resolved per clause with explicit mutable polarity taking precedence.
- V4-03: Solver V2 now runs real CP-SAT as primary and never mislabels enumeration as OR-Tools.

## Safety and autonomy

The implementation uses an autonomy envelope, not a blanket low-permission AI rule. Reversible activity replans can execute automatically when mission and traveler policy both allow the cost, loss, schedule drift, activity type, provider state, and commitment impact. Over-budget recovery remains pending confirmation. A mission-protected activity produces no feasible recovery rather than being silently changed. Existing step-up behavior for protected commitment management remains intact.

## Verification

- Python: `321 passed, 2 skipped, 2 warnings`.
- Browser: `5 passed`.
- Build: Vite production build passed.
- Static quality: Ruff check/format and compileall passed.
- Contract: OpenAPI `55/55` exact parity.
- Package: `CityNexus-Proactive-Journey-Guardian-V4-Final-20260911.zip` extracted successfully and replayed the focused V4 suite from the extracted tree.

The first packaging draft was rejected by the fresh replay because it omitted `data/mock`. The final archive was rebuilt with runtime seed data and scripts; the second extraction passed 31 focused V4 tests, OpenAPI parity, compileall, a clean secret scan, `npm ci`, and a production frontend build. Only the rebuilt archive is delivered.

The warnings are pre-existing Starlette/httpx deprecation notices. The skipped checks require live external services.

## Honest external status

- `NATIVE_DEEPSEEK_MODEL_BACKED`: `NOT_RUN_NO_CREDENTIAL`. The strict compiler and native tool loop are implemented; no live call is claimed.
- `HERMES_MODEL_BACKED`: `NOT_RUN_NOT_AVAILABLE`. No Hermes endpoint, credential, or CLI was available. The runtime adapter is present, but no literal Hermes inference run is claimed.
- `ORTOOLS_CP_SAT_V2`: `PASS` using installed OR-Tools 9.15.
- `GUARDIAN_E2E`: `PASS` in backend integration and real-browser Playwright.
- `LIVE_VALHALLA`: `NOT_RUN_NOT_CONFIGURED`; frozen mock-mobility route evidence was used.
- `PHOENIX`: `NOT_RUN_NOT_INSTALLED_OPTIONAL`.
- `PROMPTFOO`: `NOT_RUN_NOT_INSTALLED_OPTIONAL`.

## Remaining product work

The V4 milestone is complete. Sensible next steps are operational rather than correctness blockers: connect a real Hermes runtime, run credentialed DeepSeek evaluation, add a production scheduler/queue that invokes the scan endpoint, and add Phoenix/Promptfoo observability once those services are selected.
