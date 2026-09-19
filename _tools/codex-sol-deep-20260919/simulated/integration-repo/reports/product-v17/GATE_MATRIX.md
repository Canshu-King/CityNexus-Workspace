# V17 Gate Matrix

| Gate | Result | Evidence |
| --- | --- | --- |
| Semantic envelope focused tests | PASS — 8 | `backend/tests/test_v17_semantic_compiler.py` |
| V16 integration + V15 Copilot | PASS — 16 | focused regression |
| Agent runtime/Gateway focused tests | PASS — 26 | mission, runtime gate, V2 authority |
| V14 recovery/trial reference tests | PASS — 4 | V14 reference regression |
| MCP V1/V2 boundary | PASS — 6 | `agent-mcp/tests/test_mcp_boundary.py` |
| Official Hermes MCP discovery | PASS — connected, 11 tools | `hermes mcp test citynexus` |
| DeepSeek live semantic canary | NOT CONFIGURED | no process credential |
| Broad backend regression | PASS — 417 passed, 2 skipped | final `pytest -q` |
| Frontend production build | PASS — Vite 7.3.6, 1901 modules | `npm run build` |
| Native Hermes model mission | NOT CONFIGURED | no provider credential; no false claim |
| Fresh-extract targeted gate | pending package | run once after release assembly |

The two dependency warnings are existing FastAPI/Starlette/httpx deprecation
warnings and do not change gate status.
