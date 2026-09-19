# Hermes Integration Status

## V18.1 activation (2026-09-15)

- Official profile: `citynexus` (resolved by `hermes -p citynexus`)
- Hermes Agent: 0.21.2
- Provider/model: DeepSeek / `deepseek-v4-flash`
- MCP: connected, exactly 11 CityNexus V2 tools; unrelated toolsets disabled
- Gateway: loopback `127.0.0.1:8652`, Runs + SSE + stop reachable
- Native mission: **PROVEN** through Copilot; runtime identity `HERMES_NATIVE_MCP`
- Real event evidence: `mcp__citynexus__list_replans` (`tool.started` and `tool.completed`)
- Safety: PLAN_ONLY; no plan, commitment, booking, payment, or mutation occurred
- Fallback: remains available when native gateway is unavailable

Checked-in MCP status: **V2 SERVER / PASS**. The official Hermes Agent
0.21.2 is installed in the Windows user profile, and the external `citynexus`
profile is restricted to the eleven CityNexus MCP V2 tools with resources and
prompts disabled.

CityNexus now exposes a server-side native Hermes capability check, Runs API
submission, run status, approval/stop boundary, and SSE progress proxy. The
frontend only labels Hermes active when the server returns a real native run.

Current process status: **NATIVE MODEL NOT CONFIGURED**. No DeepSeek provider
credential and no loopback Hermes `API_SERVER_KEY` are configured, so this
release does not claim native Hermes inspect, PLAN_ONLY, or policy-gated model
missions. The existing OpenAI-compatible adapter remains labeled
`HERMES_COMPAT_ENDPOINT`.

No credential is stored in the repository, user-facing reports, or release
archive.
