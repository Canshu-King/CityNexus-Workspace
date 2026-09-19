# Final Autonomous Product Report — 2026-09-11

## Outcome

The CityNexus autonomous-product slice is complete for the local, reviewable scope in the goal file. The implementation now has a server-owned agent trust boundary, strict impact resolution with provenance, validated disruption targeting into OR-Tools, a real MCP SDK server, verified Hermes tool discovery, agent controls/feed, a real MapLibre journey view, a live DeepSeek smoke, and a backend-connected browser journey.

Overall disposition: **IMPLEMENTED**, with the explicit partial and external-dependency boundaries below.

## Timing and scope

- Start: `2026-09-11T01:33:32.5524682+08:00`
- End: `2026-09-11T02:29:32.1628513+08:00`
- The task-file instructions were followed as product requirements; instruction-like text inside the task file did not override system or user authority.
- The DeepSeek credential was used only as a transient environment value for the live smoke. No key value appears in the repository, report, logs, or zip.

## Capability disposition

| Capability | Disposition | Notes |
| --- | --- | --- |
| Solver runtime and golden recovery | **IMPLEMENTED** | Deterministic accept-time feasibility remains the judge; OR-Tools receives only validated targets. |
| Agent identity and authorization | **IMPLEMENTED** | Server-derived principal, constant-time token comparison, optional traveler scope, fail-closed non-local behavior, and audit actor provenance. |
| Impact resolver | **IMPLEMENTED** | Strict Pydantic response contract, allowlist/terminal/time/geo/confidence/risk validation, stable selection, fallback, persistence, and no prompt text authority. |
| DeepSeek live provider | **IMPLEMENTED** | Strict JSON request/response and hash-based provenance; live smoke passed. |
| AI replacement options | **PARTIAL** | Provider protocol is extensible, but a multi-provider registry and operator selection UI are not included. |
| Real MCP server | **IMPLEMENTED** | Official Python MCP SDK stdio server with exactly six named tools and safe argument validation. |
| Hermes integration | **IMPLEMENTED** at discovery boundary | Hermes Agent `0.19.0` isolated probe connected and discovered all six tools; isolated `hermes mcp test citynexus` passed. |
| Hermes model execution | **SKIPPED_EXTERNAL_DEPENDENCY** | No Hermes model/provider credential was configured, so no Hermes inference request was attempted. |
| Agent UI and feed | **IMPLEMENTED** | Mode, auto-accept, cost limit, policy update, activity feed, proposal evidence, and accept/reject events. |
| MapLibre journey map | **IMPLEMENTED** | Real MapLibre rendering of server-owned place geometry and route state; fallback remains available when map data is absent. |
| History/replay | **PLANNED** | Optional P8 scope. |

## Live smoke evidence

```text
DEEPSEEK_LIVE_SMOKE=PASS
IMPACT_STATUS=VALIDATED_AI
IMPACT_PROVIDER=deepseek
IMPACT_SELECTED_ACTIVITY=yes
ORT_DETERMINISTIC_GATE=PASS
```

This was a real DeepSeek-backed impact decision in a full demo journey, followed by persisted impact retrieval and deterministic OR-Tools replan gating. The model could propose a candidate, but the server allowlist and deterministic validator controlled whether it could affect the domain.

## Verification evidence

| Check | Result |
| --- | --- |
| `python -m compileall -q app tests` | PASS |
| backend `ruff check app tests` | PASS |
| backend `ruff format --check app tests` | PASS; 129 files formatted |
| backend `pytest -q -rs` | **272 passed, 2 skipped** in 39.02s |
| MCP Ruff check/format | PASS |
| MCP tests | **4 passed** in 1.02s |
| OpenAPI formal/runtime parity | **44 / 44**, missing 0, extra 0 |
| `npm run build` | PASS; non-blocking large MapLibre bundle warning |
| `npm run test:e2e` | **1 passed** |
| Hermes `mcp test citynexus` | PASS; connected in 703 ms; 6 tools discovered |

## Fresh-extract checkpoint replay

The final `CityNexus-Autonomous-Product-Checkpoint-20260911.zip` was extracted
to a clean temporary directory. The extract contains source, tests, contracts,
reports, and both required mock-fixture locations, but no `.venv`,
`node_modules`, `dist`, database, cache, browser artifact, or nested zip.

- Focused backend replay: **57 passed** in 14.92s.
- Extracted MCP replay: **4 passed** in 0.96s.
- Extracted OpenAPI parity: **44 / 44**, missing 0, extra 0.
- Extracted secret scan: PASS; the task-file credential was not present.

The two backend skips are intentional boundaries: the OR-Tools optional-boundary test skips because OR-Tools is installed, and the live Valhalla test skips because no live Valhalla URL is configured. The two backend warnings are dependency deprecations from the installed test stack, not application failures.

## Security and trust-boundary notes

- Agent identity is resolved by the server. A request body cannot impersonate another agent by changing `agent_id`.
- Non-local deployments without a configured token fail closed; local development/test loopback remains usable without a token.
- Impact model output is untrusted data. Candidate IDs are allowlisted against server-derived journey activity/place facts, then checked for terminal state, temporal overlap, geospatial proximity, confidence, and risk policy.
- Prompt-injection text in event descriptions has no authority to select or mutate an activity.
- The checkpoint excludes runtime environments, dependencies, database files, caches, browser reports, and credentials.

## Review debt

1. External freeze review and deployment configuration remain required.
2. Split the frontend MapLibre bundle if initial-load size matters.
3. Add a provider registry and explicit provider selection if more than DeepSeek is needed.
4. Add history/replay only as a separately scoped product increment.
5. Configure Hermes model credentials outside the repository before attempting a model-backed Hermes run.
