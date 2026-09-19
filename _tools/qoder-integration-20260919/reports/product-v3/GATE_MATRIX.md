# V3 Gate Matrix — Evidence Summary

| Gate | Evidence level | Repository evidence |
| --- | --- | --- |
| AIV3-01 | FROZEN_PASS | `test_gpt_agent_authority_v3.py` rejects USER_CONFIRMATION for step-up. |
| AIV3-02 | PROTOCOL_VERIFIED | MCP V2 stdio discovery returns all 11 V1+V2 tools. |
| AIV3-03 | FROZEN_PASS | Bare WEBAUTHN label is rejected; demo proof is process-scoped and constant-time checked. |
| LIVE-01 | MODEL_BACKED | Real DeepSeek provider call completed in the supplied transient-credential smoke. |
| LIVE-02 | PROTOCOL_VERIFIED | V2 MCP server and Gateway catalog expose the coherent inspect/plan/action surface. |
| LIVE-03..05 | MODEL_BACKED | DeepSeek selected the sequence; inspection preceded mutation; no fixed order in the driver. |
| LIVE-06 | E2E_VERIFIED | AgentRunStep rows and GET run reload persisted tool results. |
| LIVE-07 | E2E_VERIFIED | Provider failure persists a skipped/degraded run without mutating Journey truth. |
| MIS-01..05 | E2E_VERIFIED | Mission compiler, protected ID resolution, envelope bounds, and in-envelope auto execution tests. |
| IMP3-01..06 | FROZEN_PASS | Fuzzy alias, polygon, route intersection, time, primary/secondary, protected risk-only tests. |
| ALT-01..05 | E2E_VERIFIED | Server Place search, materialization, feasibility, and autonomous low-risk replacement tests. |
| SOL2-01..07 | INTEGRATED | Pure V2 contract tests plus endpoint materialization/acceptance test; V1 suite remains green. |
| UI-01..06 | E2E_VERIFIED | Playwright Control Tower suite covers command, trace, map/route evidence, policy, and reload. |
| E2E-01 | PARTIAL / HONEST | DeepSeek + MCP-compatible backend path passed; literal Hermes CLI was unavailable. |

The evaluator should distinguish `MODEL_BACKED` CityNexus orchestration from a
literal Hermes executable run. The former is verified; the latter is an
external environment boundary, not silently inferred from MCP compatibility.
