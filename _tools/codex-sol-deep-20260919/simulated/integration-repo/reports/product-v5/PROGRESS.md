# CityNexus Live Journey Autopilot V5 — Progress

Date: 2026-09-12

The supplied V5 assist package was treated as the implementation contract. Its instructions were kept distinct from the user's request: the user requested execution in the current CityNexus workspace; the package supplied the V5 requirements, external findings, gate matrix, and test artifact.

## Current status

The V5 completion gate is green. The browser flagship starts a Journey, activates a standing mission, starts the server-owned Autopilot, changes a provider fixture, and reaches an executed recovery without posting `/guardian/scan` or opening a new chat prompt. The persisted operation history, protected Cruise/Dinner/C4 state, route evidence, and active Plan survive reload. Repeating the same semantic provider signal does not create another Guardian recovery or PlanVersion.

The implementation also passes the offline deterministic fallback path and a real native DeepSeek smoke. No Hermes endpoint was configured in the workspace, so Hermes is reported separately as `NOT_RUN_EXTERNAL`.

## External V4 findings verified against the workspace

| Finding | Verification and disposition |
| --- | --- |
| Guardian used a fixed deterministic controller | Confirmed in the V4 code. `scan_guardian()` now attempts `configured_journey_agent()` first, normalizes the AgentRun/tool trace, and retains the deterministic controller only for `AgentRuntimeUnavailable`. |
| Proactive browser flow manually created events and posted `/guardian/scan` | Confirmed in the V4 browser scenario. V5 adds the server-owned signal pipeline, provider fixture ingestion, Guardian pulse worker, and a browser test that observes zero `/guardian/scan` requests. |
| `cooldown_until` was decorative | Confirmed. Semantic incident fingerprints and a real cooldown check now suppress equivalent refreshes while preserving observation updates. |
| Mission Compiler could widen numeric authority | Reproduced with the supplied `test_gpt_v5_mission_authority.py`. Model values are now intersected with deterministic raw-text caps and the persisted `resolved_intent` is intersected again with traveler policy. |
| Model mutable references could erase explicit protection | Reproduced and fixed. Deterministically protected Activity IDs are unioned first and removed from model-derived mutable IDs. |
| Unresolved model references were discarded | Reproduced and fixed. Unresolved model references persist in `unresolved_references_json` and receive no authority. |
| V4 package hygiene was inaccurate | Confirmed by the supplied review. V5 packaging uses an explicit staging allowlist plus exclusion scan for dependencies, caches, databases, browser reports, nested archives, and credentials. |

## Delivered implementation

- Server-owned `ProviderObservation`, `CitySignalFixture`, and `GuardianPulse` persistence.
- Demo and live-provider refresh seam using the same ingestion contract; mobility snapshots compare frozen baseline/current estimates and emit semantic `TRAFFIC_DELAY` evidence only when the delta is meaningful.
- Configurable, single-instance Guardian worker with `CITYNEXUS_GUARDIAN_AUTORUN`, interval, provider, and cooldown settings. Tests leave it disabled unless explicitly started.
- Semantic incident fingerprinting, evidence refresh, cooldown enforcement, and repeated-signal deduplication.
- Configured runtime routing: Hermes when configured, native DeepSeek otherwise, deterministic Guardian fallback on runtime unavailability.
- Gateway support for server-grounded AI-only semantic targets inside an authorized reversible envelope; deterministic feasibility remains the hard post-action gate.
- Backend operations SSE and Control Tower rendering of persisted Observation, AI Inference, Optimization, Policy, and Domain Mutation evidence.
- Zero-touch Playwright flagship and negative coverage for stale-cleared signals, protected commitments, over-budget policy, provider degradation, runtime fallback, reload, and repeat deduplication.
- MCP V2 test import path is now part of the backend test configuration, keeping the V1 planning tools visible in the V2 builder test.

## Validation completed

- Supplied Mission Authority replay: 3 passed.
- Focused V5/contract/Guardian/Solver/Mission gate set: 13 passed.
- Full backend regression: **320 passed, 2 skipped, 2 warnings**.
- `ruff check app tests`: passed.
- `ruff format --check app tests`: passed.
- Python `compileall`: passed.
- Frontend production build: passed; Vite emitted only its existing large-chunk advisory.
- Full Playwright suite: **6 passed**.
- Native DeepSeek live smoke using the supplied temporary key in process memory: completed with provider `deepseek`, model `deepseek-chat`, executed recovery, and model-selected trace `inspect_journey → inspect_twin → list_replans → search_city_services → request_replan → list_replans → accept_replan`.
- Deterministic fallback smoke/E2E: completed with `citynexus-guardian / deterministic-recovery-controller-v1`.

## Remaining optional boundaries

Hermes model-backed execution was not run because no Hermes endpoint/key was configured. Live Valhalla, Phoenix/OpenInference, and Promptfoo were not required to make the zero-touch gate green and are explicitly labeled in the final gate matrix. The final archive contains no temporary key, dependency directory, database, cache, browser report, or nested review archive.
