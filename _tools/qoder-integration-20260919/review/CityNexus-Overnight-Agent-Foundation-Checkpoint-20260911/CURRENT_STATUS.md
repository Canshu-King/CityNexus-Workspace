# CityNexus Overnight Agent Foundation

Status: **IMPLEMENTED / local gates green / external freeze pending**

The checkpoint contains Solver Runtime V1 hardening and the Agent Runtime
Foundation. The Agent path is server-owned:

```text
Agent/MCP intent -> safe allowlist -> persisted traveler policy
-> server-derived proposal/Event/Journey/C4 facts
-> deterministic accept-time feasibility gate -> domain mutation
```

Solver remains a candidate generator and CityNexus deterministic feasibility
remains the judge. `request_replan` creates a PRESENTED proposal only.
`accept_replan` can activate a proposal only after policy authorization and the
existing accept-time gate. C4 commitments are remapped and preserved by the
existing domain operation.

Local evidence: 251 backend tests passed, 2 skipped; Agent gate 16 passed;
MCP boundary 3 passed; OpenAPI formal/runtime 43/43; compileall and Ruff
passed; frontend build and backend-connected Playwright passed.

