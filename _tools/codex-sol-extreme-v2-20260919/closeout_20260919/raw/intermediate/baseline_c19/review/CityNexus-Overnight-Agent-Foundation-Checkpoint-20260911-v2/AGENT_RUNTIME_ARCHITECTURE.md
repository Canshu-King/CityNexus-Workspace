# Agent Runtime Architecture

See [`contracts/AGENT_RUNTIME_ARCHITECTURE.md`](contracts/AGENT_RUNTIME_ARCHITECTURE.md)
for the contract. The implementation is in `backend/app/agent/` and the
HTTP surface is `/api/v1/agent/tools/{tool_name}`.

Only six tools are exposed. Read tools do not activate plans. Replan requests
are proposal-only. Acceptance derives all trusted facts on the server and
delegates the final state change to the existing deterministic operation.

