# V17 Hermes Native MCP Evidence

Date: 2026-09-14

## Runtime

- official Hermes Agent: `0.21.2 (2026.9.11)`;
- official managed Python: `3.11.16`;
- configuration location: Windows Hermes user profile, outside the release;
- configured server: `citynexus` stdio, V2 mode, resources/prompts disabled;
- selected tools: exactly eleven CityNexus V2 tools.

No credential, token, raw prompt, or hidden reasoning is recorded here.

## Protocol proof

The official Hermes command completed successfully:

```text
hermes mcp test citynexus
✓ Connected (2157ms)
✓ Tools discovered: 11
```

The official Hermes Python environment uses MCP 2, so CityNexus now exposes
the same V2 contract through its low-level MCP 2 server branch. The pinned
MCP 1.x FastMCP path remains available for the repository runtime. Direct MCP
boundary tests passed **6/6**, and an official MCP 2 stdio initialize/tools-list
probe discovered the same eleven names.

Discovered tool names:

`inspect_journey`, `inspect_twin`, `list_replans`, `search_city_services`,
`request_replan`, `accept_replan`, `replace_activity`,
`reschedule_activity`, `create_booking`, `cancel_refundable_booking`,
`request_commitment_change`.

## Agent proof status

The native Hermes model loop is **NOT CONFIGURED** because no provider
credential was present. Therefore the three model-driven scenarios are not
claimed as completed:

1. native Hermes read-only inspection;
2. native Hermes PLAN_ONLY proposal;
3. native Hermes policy-gated action.

The CityNexus side of those boundaries is covered by the existing Agent
runtime/Gateway tests: inspection is required before mutation, PLAN_ONLY blocks
mutation, and the Gateway returns its policy decision for protected/high-risk
actions. The existing OpenAI-compatible `HermesJourneyAgent` remains labeled
`HERMES_COMPAT_ENDPOINT`, never native Hermes.
