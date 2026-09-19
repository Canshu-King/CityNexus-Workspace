# Agent Runtime Architecture V3

See [`contracts/AGENT_RUNTIME_ARCHITECTURE.md`](contracts/AGENT_RUNTIME_ARCHITECTURE.md)
for the contract. The implementation is in `backend/app/agent/` and the
HTTP surface is `/api/v1/agent/tools/{tool_name}`.

The pinned V1 catalog has six tools; the V2 runtime/MCP builder exposes all
eleven inspect, planning, and typed-action tools in one coherent session. Read
tools do not activate plans. Replan requests are proposal-only. Acceptance and
typed actions derive all trusted facts on the server and delegate final state
changes to deterministic feasibility/business-fact gates.

The natural-language `/agent/commands` path persists a JourneyMission and
AgentRun. A model-selected tool trace is persisted as AgentRunStep rows and can
be reloaded from `/journeys/{journey_id}/agent/runs/{run_id}`. DeepSeek is an
external model boundary; a missing or failed provider leaves Journey truth
unchanged and records a degraded/skipped run.
