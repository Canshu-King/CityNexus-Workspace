# Overnight gate matrix

| Stage | Evidence | Result |
| --- | --- | --- |
| WP06 follow-up | backend regression and focused replan tests | PASS |
| F3 Opportunity Window | fit, boundary, closed/budget, C4-preservation tests | PASS |
| Multi-candidate scoring | verified ranking and lower-disruption tie ordering | PASS |
| Valhalla/MobilitySnapshot | offline adapter, timeout/malformed, snapshot tests | PASS; live optional skip |
| Open-Meteo | mocked parser, frozen facts, provider event and recovery tests | PASS |
| OR-Tools | optional candidate boundary and common gate tests | PASS; package not installed |
| LiteLLM/DeepSeek | verified-facts contract and resilient fallback tests | PASS; credentials absent |
| Journey Mode UI | Vite build and contract selectors | PASS |
| Playwright | expanded golden scenario | 1 passed |
| API contract | OpenAPI 3.1 exact operation set | 38/38 PASS |
| Full backend | deterministic regression suite | 149 passed, 1 skipped |

