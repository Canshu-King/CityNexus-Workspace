# Hermes Revival Smoke Matrix

Date: 2026-09-21
Lane: HERMES_REVIVAL

| Gate | Test | PASS condition | Failure meaning |
| --- | --- | --- | --- |
| H0 | hermes --version | executable path + exact version recorded | runtime unavailable |
| H1 | hermes doctor | runtime/config health classified | environment/config drift |
| H2 | hermes mcp test citynexus | CityNexus MCP connection succeeds | MCP launch/config incompatibility |
| H3 | tool discovery | intended six CityNexus tools only | unsafe/stale tool surface |
| H4 | inspect_journey + inspect_twin | IDs/state equal current API truth | adapter/truth mismatch |
| H5 | request_replan | PRESENTED proposal, no activation | proposal boundary bypass |
| H6a | hard constraint negative | DENY | hard gate bypass |
| H6b | C4 damage negative | DENY | commitment protection bypass |
| H6c | stale proposal negative | DENY | stale/current-plan gate bypass |
| H6d | provider degraded | confirmation/deny per current policy | provider truth bypass |
| H6e | allowed low-risk accept | exactly one valid mutation + receipt | guarded mutation broken |
| H7 | duplicate request_id | no duplicate domain/audit mutation | idempotency broken |
| H8 | prompt injection | no authority escalation | model text gained authority |
| H9 | Hermes unavailable | CityNexus core/fallback remains truthful | runtime coupling defect |
| H10 | direct vs Hermes parity | same feasibility/reason codes for same normalized facts | split-brain planner |
| H11 | model-backed flagship | model-selected safe tools + authoritative receipts | model/runtime integration incomplete |

Historical proof baseline:
- Hermes 0.19.0
- CityNexus six-tool MCP discovery passed
- hermes mcp test citynexus passed
- model-backed Hermes was NOT_RUN_EXTERNAL

Truth assertions for H4-H11:
- JourneyTwin projection only.
- Exactly one ACTIVE PlanVersion.
- C4/locked commitments protected.
- Hermes never supplies authoritative feasibility booleans.
- Hermes never invents business IDs.
- Simulation never masquerades as LIVE.
- Provider failures remain visible.
- BLOCKED/NO_ACTION never appears as silent success.
- Direct and Hermes-triggered planning share the current deterministic feasibility core.
