# Hermes Integration Status — V18.3 (2026-09-15)

- Official Hermes Agent: 0.21.2
- Official profile: `citynexus`, resolved by `hermes -p citynexus`
- Provider/model: DeepSeek / `deepseek-v4-flash`
- MCP: CityNexus V2, exactly 11 allowlisted tools
- Gateway: loopback Runs + SSE + stop boundary
- Native proof: **PROVEN** through Copilot with actual CityNexus MCP tool events
- Runtime identity: server/run data; `DIRECT` until native execution is observed
- Safety: PLAN_ONLY; Gateway/Guardian remain authoritative for proposals,
  approvals, bookings, payment, commitments, and mutations

The capability contract is shape-stable in every branch, including
`ready: false` when native Hermes is unconfigured or unreachable. The frontend
does not infer Hermes from the existence of a timeline.

The reused Windows User-scope DeepSeek credential is passed only to child
processes when present. A random API-server key is process-local to the
localhost gateway. Neither is stored in this repository or release archive.

Two bounded DeepSeek Responses checks timed out during the V18.2/V18.3 window;
fallback and unavailable states remain truthful. See
`reports/product-v18-3/HERMES_RUNTIME_EVIDENCE.md`.
