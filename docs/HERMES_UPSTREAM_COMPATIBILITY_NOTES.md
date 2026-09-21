# Hermes Upstream Compatibility Notes for CityNexus

Research date: 2026-09-21
Purpose: give Qoder concrete current-upstream facts before reviving the historical CityNexus Hermes integration.

## Current stable target

Official NousResearch/hermes-agent releases list Hermes Agent v0.21.3 as Latest, release tag v2026.9.14, released 2026-09-14.

Historical CityNexus evidence was on Hermes Agent 0.19.0.

This is a meaningful version gap. Treat current-stable compatibility as a migration trial, not a drop-in restart.

## Why isolation is mandatory

The v0.21.x release line includes substantial session/state and MCP/runtime work. In particular:
- v0.21.2 is explicitly a state.db patch release after a large session-store rewrite.
- releases after 0.20.x include MCP authorization/protocol work.
- current Hermes supports much broader built-in tooling than the old narrow CityNexus product profile needs.

Therefore:
- preserve the old Hermes data/config before touching it;
- use a separate HERMES_HOME for current stable;
- pin the release tag during the compatibility trial;
- do not run hermes update against the only copy of the historical profile.

## Native Windows facts

Current official docs support Windows 10/11 natively.

The installer supports:
- Branch
- Commit
- Tag
- HermesHome
- InstallDir
- SkipSetup

This makes an isolated CityNexus trial straightforward:
- dedicated install directory;
- dedicated HERMES_HOME;
- exact release tag;
- no admin requirement;
- no need to mutate the user's global Hermes profile.

Qoder should prefer exact-version isolation over upgrading a shared install.

## MCP filtering is now a first-class control

Current Hermes MCP config supports per-server tool policy:
- tools.include
- tools.exclude
- resources
- prompts

If include is configured, only the listed server-native MCP tools are registered.

For CityNexus this is the right boundary. The revival profile should whitelist only:

- inspect_journey
- inspect_twin
- list_replans
- search_city_services
- request_replan
- accept_replan

and set MCP prompts/resources off unless CityNexus later has an explicit use for them.

This is stronger than relying on model instructions saying “do not call dangerous tools”.

## Built-in Hermes toolsets are broad

Current hermes-cli is intentionally broad. Official docs describe a default CLI platform including filesystem, terminal, web, browser, memory, skills, delegation, code execution, cron and other tooling.

That is useful for a general autonomous agent, but it is the wrong default trust surface for the CityNexus product agent.

Qoder must inspect the exact installed version with Hermes tool-management commands, then disable unnecessary built-in toolsets for the product profile. Do not assume an old toolset name remains valid.

The design goal is:
Hermes reasons -> CityNexus safe MCP/Gateway -> CityNexus decides truth.

Not:
Hermes reasons -> shell/database/browser -> silently mutates truth outside CityNexus.

## DeepSeek route

Current Hermes docs list DeepSeek as a built-in provider using DEEPSEEK_API_KEY and provider key deepseek.

For CityNexus revival:
- DeepSeek is a reasonable first model-backed Hermes route if a safe process-scoped credential is already available.
- Credential material belongs only in the isolated Hermes environment/.env.
- Do not duplicate it into CityNexus source or committed config.
- Do not block MCP/read-only/guarded deterministic smoke work just because the model credential is absent.

## Exact migration question Qoder must answer

The core compatibility question is not “can Hermes start?”

It is:

Can current Hermes call the current CityNexus MCP boundary while preserving all current server-owned truth rules?

Required comparison:
1. historical 0.19.0 tool discovery;
2. current stable v0.21.3 tool discovery;
3. old six-tool schemas;
4. current Gateway/MCP schemas;
5. auth/principal mapping;
6. request_id/idempotency behavior;
7. proposal/accept receipts;
8. current AgentOutcome semantics;
9. current direct-vs-AI planner parity;
10. current DestinationCapability/mobility evidence semantics.

Only compatibility changes at the MCP adapter should be preferred. Do not push model/runtime-specific semantics into the domain layer.

## Recommended first 30-60 minute execution block

1. Locate old Hermes executable/config.
2. Record version and profile paths.
3. Extract V18.1/V18.2/V18.3 Hermes artifacts.
4. Read HERMES_INTEGRATION_STATUS.md and contracts/HERMES_MCP_BOUNDARY.md.
5. Identify the exact current agent-mcp entrypoint.
6. Attempt historical hermes mcp test citynexus without mutating production.
7. Create isolated current-stable HERMES_HOME/install.
8. Pin v2026.9.14.
9. Run version + doctor.
10. Configure CityNexus MCP with exact six-tool include.
11. Run MCP test and tool-surface diff.
12. Return a checkpoint before any production adapter write.

That checkpoint should contain evidence, not prose claims.
