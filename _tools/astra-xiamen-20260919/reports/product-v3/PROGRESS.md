# CityNexus Autonomous City Intelligence V3 Progress

Date: 2026-09-11

The archive instructions were treated as product requirements and merged with
the current repository. Existing user work was preserved; no reset or cleanup
was used.

| Area | Status | Evidence |
| --- | --- | --- |
| P0 step-up correctness | FROZEN_PASS | REQUIRE_STEP_UP requires a verified STEP_UP proof; ordinary confirmation and a bare WEBAUTHN label are rejected. |
| MCP V2 | PROTOCOL_VERIFIED | One V2 stdio server exposes the coherent 11-tool inspect/plan/action surface; V1 six-tool default remains compatible. |
| DeepSeek agent | MODEL_BACKED | Real DeepSeek OpenAI-compatible tool loop selected its own tool calls for the Chinese mission; no fixed order in the smoke driver. |
| Mission / AgentRun | E2E_VERIFIED | Structured one-run mission, persisted run/steps, reload endpoint, and degraded provider path. |
| Impact Intelligence V3 | FROZEN_PASS | Fuzzy aliases, temporal evidence, polygon containment, LineString intersection, primary/secondary risks, protected risk-only handling. |
| Alternative discovery | E2E_VERIFIED | Server-owned Place search and materialization; no donor Activity required; feasibility rechecked. |
| Solver V2 | INTEGRATED | Explicit `CITYNEXUS_SOLVER=v2` multi-slot Top-K path; V1 remains the default and fallback. |
| Control Tower | E2E_VERIFIED | Natural-language command, persisted run trace, mission metrics, map disruption scope/risk styling, reload. |
| Hermes CLI | EXTERNAL_BOUNDARY | Hermes binary/provider runtime was not installed in this workspace; MCP protocol and backend DeepSeek adapter are verified separately. |
| Live Valhalla / production identity | OPTIONAL FOLLOW-ON | No live Valhalla URL or production WebAuthn deployment was configured. |

## Live model evidence

The supplied temporary DeepSeek credential was loaded only into a child
process environment for the smoke run. It was not printed, persisted, placed
in audit data, copied into frontend files, or included in the final package.

The model-selected run inspected the Journey/Twin, listed replans, searched
server-owned services, requested a replan, inspected the result, and accepted
the bounded low-risk change. The persisted run completed with protected C4
commitments intact. This is `MODEL_BACKED` CityNexus orchestration, not a claim
that the Hermes CLI itself was installed or executed.
