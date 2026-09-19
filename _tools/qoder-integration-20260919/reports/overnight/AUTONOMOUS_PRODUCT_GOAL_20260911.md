# Autonomous Product Goal — 2026-09-11

Status: **HISTORICAL BASELINE / superseded by product-next continuation below**

## Run record

- Start: `2026-09-11T01:33:32.5524682+08:00`
- Checkpoint scope: CityNexus solver, agent gateway, impact resolution, MCP/Hermes boundary, agent UI, map, and regression evidence.
- User-supplied instructions were treated as task requirements. Secrets in the task file were never copied into source, reports, logs, or the checkpoint.

## Initial truth

- OR-Tools was installed at `9.15.6755`; the project virtual environment used Python `3.12.14` and Node `24.14.0` / npm `11.9.0`.
- The initial focused backend baseline was 46 passed / 1 skipped when run from the correct project directory.
- The previous checkpoint had the solver and first agent foundation, but no persisted impact-assessment contract, no real MCP SDK server entrypoint, no authenticated agent-principal boundary, and no production-shaped agent/map UI.
- Hermes was not installed in the application environment at the beginning.

## Completed milestones

| Area | Status | Evidence |
| --- | --- | --- |
| P0 solver/agent/MCP/provider/weather/golden replay | **IMPLEMENTED** | Full backend and focused suites green; OR-Tools runtime gate remains deterministic. |
| Agent principal boundary | **IMPLEMENTED** | Server-owned principal resolution; body `agent_id` is ignored; configured token path and local development path tested. |
| P1 strict impact contract and 15-case matrix | **IMPLEMENTED** | `backend/app/intelligence/impact_contract.py`, validation/resolver modules, and 16 impact tests. |
| P2 validated impact into OR-Tools | **IMPLEMENTED** | Selected validated activity is the only disruption target admitted to replanning; IMP16 covers the integration. |
| P3 AI provider/provenance | **PARTIAL** | Pluggable provider protocol, strict JSON, provider/model/status/hash provenance, and DeepSeek implementation are present; multi-provider replacement registry/UI is future work. |
| P4 Hermes integration | **IMPLEMENTED** at protocol boundary | Hermes Agent `0.19.0` isolated probe connected to the stdio server and discovered all six tools; `hermes mcp test` passed. |
| P4 Hermes model run | **SKIPPED_EXTERNAL_DEPENDENCY** | No Hermes inference provider/model credential was configured; no model call was made from Hermes. |
| P5 agent UI/feed/policy controls | **IMPLEMENTED** | Advisory/assisted/autonomous controls, cost/auto-accept settings, activity feed, evidence summary, and policy API wiring. |
| P6 MapLibre journey map | **IMPLEMENTED** | Real `maplibre-gl` map with server-owned place coordinates, old/new GeoJSON paths, activity markers, disruption marker, and offline-safe fallback. |
| P7 golden E2E story | **IMPLEMENTED** | `frontend/e2e/golden.spec.ts` passed against the live backend. |
| P8 history/replay UI | **PLANNED** | Optional scope not required for the validated product slice. |

## Live DeepSeek smoke

The key from the task file was loaded only into the transient process environment for the smoke command. It was not printed, persisted, or included in artifacts.

```text
DEEPSEEK_LIVE_SMOKE=PASS
IMPACT_STATUS=VALIDATED_AI
IMPACT_PROVIDER=deepseek
IMPACT_SELECTED_ACTIVITY=yes
ORT_DETERMINISTIC_GATE=PASS
```

The live path exercised a full backend journey: demo reset, plan/select, booking and capture, activity start/complete, ambiguous closure text without an activity id, AI impact resolution, persisted assessment retrieval, proposal generation, and deterministic OR-Tools gating.

## Final local verification

- Backend: `272 passed, 2 skipped` in `39.02s`.
- Backend compilation: PASS.
- Backend Ruff check and format check: PASS (`129 files already formatted`).
- MCP package: `4 passed`.
- MCP Ruff check and format check: PASS.
- OpenAPI parity: formal `44`, runtime `44`, missing `0`, extra `0`.
- Frontend production build: PASS. Vite emitted a non-blocking large-chunk warning for the MapLibre bundle.
- Playwright E2E: `1 passed`.
- Fresh-extract checkpoint replay: focused backend `57 passed`; MCP `4 passed`; OpenAPI `44/44`.
- Backend warnings: two dependency deprecation warnings from the installed test stack.
- Documented optional skips: OR-Tools boundary test (OR-Tools is installed) and live Valhalla (URL not configured).

## Files added or materially changed

- `backend/app/agent/principal.py`
- `backend/app/intelligence/impact_contract.py`
- `backend/app/intelligence/impact_validation.py`
- `backend/app/intelligence/impact_resolver.py`
- `backend/app/integrations/ai/impact_provider.py`
- `backend/app/db/models.py`, `backend/app/main.py`, `backend/app/services.py`, `backend/db/schema.sql`, `.env.example`
- `backend/tests/test_impact_resolver.py`, `backend/tests/test_agent_principal_boundary.py`
- `agent-mcp/citynexus_mcp/server.py`, `client.py`, tests, and Hermes config example
- `frontend/src/components/JourneyMap.tsx`, API/demo/main/style updates, and E2E coverage
- `contracts/openapi.yaml`, `tools/run_live_impact_smoke.py`, and verification/report files

## Remaining review items

- External freeze/review is still required before production deployment.
- Configure a real Hermes inference provider only in the operator's own environment if a model-backed Hermes run is desired.
- Consider splitting the frontend bundle and adding a multi-provider AI registry.
- Keep the live Valhalla and optional history work outside this validated checkpoint unless explicitly requested.

## Checkpoint

`CityNexus-Autonomous-Product-Checkpoint-20260911.zip` is the final clean
source checkpoint. It excludes runtime environments, dependencies, builds,
databases, caches, browser reports, old archives, and credentials.

## Product-hardening continuation — current authoritative status

The sections above document an earlier phase of the same date and are retained
for provenance. They are not current evidence for the product-next iteration.
As of `2026-09-11T16:36:00+08:00`, the current working tree has the following
verified state:

- P0–P6 product-next work is implemented at the demonstrated maturity levels;
  the latest user direction intentionally permits server-known AI semantic
  hypotheses to auto-execute when reversible, loss-free, non-protected, and
  inside the user-owned Autonomy Envelope. Deterministic gates verify the
  post-action Journey and business facts; they do not replace semantic
  judgment.
- Backend full regression: `285 passed, 2 skipped, 2 warnings`.
- MCP SDK/unit and real stdio protocol tests: `4 passed`; isolated Hermes
  Agent `0.19.0` discovered six whitelisted tools in `937 ms`.
- OpenAPI formal/runtime parity: `47/47`; compileall and Ruff checks pass.
- Frontend build passes; backend-connected Playwright passes `3/3` serially,
  including Assisted confirmation, Autonomous `ALLOW_AUTO`, persisted Feed /
  Reflect reload, and provider-backed frozen route geometry.
- Current process credential checks found no DeepSeek or Hermes model provider
  credentials. Therefore current live DeepSeek and Hermes model-backed status
  is `SKIPPED_EXTERNAL_DEPENDENCY`; the historical live-smoke claim above is
  not reused as current evidence.
- Fresh extraction and final checkpoint packaging remain the final delivery
  gates; typed action tools for replacement/rescheduling/booking/cancellation
  and live model/provider replay remain explicitly partial or follow-up work.
