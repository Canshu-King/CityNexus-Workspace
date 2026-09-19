# Test Results

Captured on 2026-09-11 from `D:\\moodle\\CityNexus` using the repository
`.venv` with `ortools==9.15.6755` installed.

| Gate | Result |
| --- | --- |
| SRH-01..05 | 5 passed |
| ORT-01..20 Solver Runtime | 20 passed |
| Solver reference/policy/optional boundary | 16 passed, 1 skipped |
| inherited Provider/Weather/Golden | 35 passed |
| AGT-01..24 DB/API gate | 16 passed |
| MCP boundary tests | 3 passed |
| full backend | 251 passed, 2 skipped |
| `python -m compileall -q app tests` | PASS |
| `ruff check app tests` | PASS |
| `ruff format --check app tests` | PASS |
| OpenAPI formal/runtime parity | 43 / 43, missing 0, extra 0 |
| frontend `npm run build` | PASS |
| frontend `npm run test:e2e` | 1 passed |

The two backend skips remain the documented optional/external dependency
boundaries. No network call is made by GET/Twin, feasibility, or proposal
candidate gating.

