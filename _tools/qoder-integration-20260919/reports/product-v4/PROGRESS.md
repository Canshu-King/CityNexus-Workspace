# Proactive Journey Guardian V4 Progress

Date: 2026-09-11

## Outcome

The V4 product milestone is implemented. CityNexus can persist a standing MissionIntent, observe unresolved city events without a new chat instruction, classify the scan as `NO_ACTION`, `WATCH`, or `RECOVERY_REQUIRED`, launch exactly one recovery run for an incident set, generate deterministic Top-K CP-SAT candidates, apply the mission/policy intersection, and activate an envelope-safe plan through the existing Agent Gateway.

## Completed work

- Reproduced and fixed all three external findings:
  - Chinese cardinal money values such as `五十元` compile to 5,000 minor units.
  - Clause-local semantic polarity keeps “游船可以取消，晚餐别动” from protecting the cruise.
  - OR-Tools CP-SAT is the Solver V2 primary path and emits `ORTOOLS_CP_SAT_V2`; the bounded enumerator is retained and honestly labeled as fallback.
- Added Mission Compiler V2 persistence: raw user text, strict intent, server-resolved activity IDs, mutable/protected sets, policy-intersected envelope, compiler/model provenance, confidence, unresolved references, and a user-safe rationale.
- Added a strict DeepSeek JSON compiler path with deterministic fallback. Model output cannot invent or authorize database IDs; the server resolves references against the active plan.
- Added Hermes-first runtime selection through an OpenAI-compatible Hermes adapter, with the existing native DeepSeek tool loop as the configured fallback.
- Integrated RapidFuzz and Shapely as primary fuzzy/geospatial impact utilities while retaining CityNexus ownership and lifecycle checks.
- Added durable `GuardianRun` state, evidence fingerprints, cooldown metadata, incident-set deduplication, normalized AgentRun tool traces, and reloadable APIs.
- Added standing Mission, scan, and status endpoints plus exact OpenAPI parity.
- Added Journey Operations UI with distinct observation, inference, solver, policy, and mutation lanes.
- Added flagship browser coverage for a weather + traffic incident set, automatic CP-SAT recovery, protected cruise/dinner, Plan/Twin mutation, old/new route evidence, trace display, and reload.

## Verification summary

- Backend + MCP: `321 passed, 2 skipped`.
- External V4 findings plus focused Mission/Guardian/Solver/Impact suites: pass.
- Frontend production build: pass.
- Playwright: `5 passed`, including the proactive Guardian flagship E2E.
- Ruff check and format check: pass after final import normalization.
- Python compileall: pass.
- OpenAPI parity: `55 formal / 55 runtime`, no missing or extra operations.

The two skipped tests are credential-dependent live provider checks. No credential, Hermes endpoint/CLI, live Valhalla endpoint, Phoenix, or Promptfoo installation was present in this environment.
