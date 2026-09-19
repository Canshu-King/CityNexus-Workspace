# V18 Gate Matrix

| Gate | Result | Evidence |
| --- | --- | --- |
| Future Event target/time authority | PASS | `test_v18_semantic_time_and_verification.py`; resolved future time uses Journey end and unresolved case is review-only |
| VERIFY_FACT bounded evidence path | PASS | source observations persist as non-authoritative evidence; no Event is created |
| Native Hermes client contract | PASS | `test_v18_hermes_native_client.py`; loopback bearer stays server-side and metadata restricts CityNexus MCP |
| V17 SemanticEnvelope regression | PASS — 8 | `test_v17_semantic_compiler.py` |
| OpenAPI runtime parity | PASS | `test_contract.py`; Hermes capability/status/SSE routes are declared |
| MCP V1/V2 boundary | PASS — 6 | `agent-mcp/tests/test_mcp_boundary.py` |
| V16 integration + V15 Copilot | PASS — 20 combined with V14 references | final focused reference run |
| V14 recovery and trial readiness | PASS | final focused reference run |
| Broad backend regression | PASS — 421 passed, 2 skipped | final `pytest backend/tests -q` |
| Frontend production build | PASS — Vite 7.3.6 / 1,904 modules | final `npm run build` |
| Desktop Playwright | PASS | fresh sealed Journey, grouped nav, Copilot EXPLAIN_PLAN |
| Mobile Playwright | PASS | Today / Map / Copilot / Wallet / Me, Copilot WHAT_IF |
| Hermes installation/profile | PASS | Hermes 0.21.2 installed; external profile and MCP V2 eleven-tool surface retained |
| Native Hermes model proof | NOT CONFIGURED | no process DeepSeek credential or loopback Hermes API server key |
| Fresh-extract release gate | PASS — 22 focused tests | fresh extraction; 474 ZIP entries; 0 forbidden entries |
