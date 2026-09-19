# CityNexus Predictive Real-City Twin V6 — Final Report

Date: 2026-09-12  
Repository: `D:\moodle\CityNexus`

## Outcome

**PREDICTIVE REAL-CITY TWIN V6 is complete.** The required completion gate is green: CityNexus predicts a Journey weakness and autonomously prevents the failure while preserving the user's protected Cruise/C4 commitment.

The final browser flow is:

```text
RISK_FORECAST
  -> composite provider observations
  -> JourneyResilienceSnapshot / PREDICTIVE_WEAKNESS
  -> six bounded counterfactuals
  -> replay-backed real-city POI discovery/materialization
  -> CP-SAT Solver V2
  -> Delegation Policy ALLOW_AUTO
  -> preemptive Plan mutation before hard failure
  -> protected commitment preserved
  -> Control Tower / MapLibre / reload evidence
```

This preserves the V5 zero-touch autonomous recovery milestone. V6 does not turn model-derived semantic judgment into an automatic confirmation requirement; it uses the deterministic layer for post-action hard facts and the Autonomy Envelope for authority.

## Delivered architecture

- Per-Journey Autopilot enrollment over a process-global worker.
- Composite weather, mobility/routing, and city-discovery provider mesh with independent state, provenance, TTL, and replay fallback.
- Open-Meteo, Valhalla, Nominatim, Overpass, and OpenFreeMap adapters.
- Server-owned real-city discovery and stable provider/external-id materialization into CityNexus domain records.
- Deterministic resilience snapshots with activity risk, commitment buffer, failure modes, recommendation, and evidence provenance.
- Bounded Counterfactual Twin simulation using JourneyTwin + CP-SAT V2 without Domain Truth mutation.
- Predictive Guardian action with durable preemptive evidence, autonomous in-envelope execution, policy gating, and high-frequency deduplication.
- Control Tower resilience and provider panels with MapLibre/OpenFreeMap metadata, route evidence, risk/C4 markers, and offline/replay evidence.

## Validation results

| Check | Result |
| --- | --- |
| V6 + V5 + V4 focused backend gates | **8 passed, 2 warnings** |
| Full backend pytest | **323 passed, 2 skipped, 2 warnings** |
| Ruff check / format check | **passed / passed** |
| Python compileall | **passed** |
| Frontend production build | **passed** |
| Full Playwright suite | **7 passed** |
| Predictive Real-City Twin flagship E2E | **passed** |
| Open-Meteo / Nominatim / Overpass / Valhalla / OpenFreeMap live smokes | **passed** |
| Native DeepSeek model-backed smoke | **passed** |
| Literal Hermes model-backed smoke | **NOT_RUN_EXTERNAL** |
| Phoenix trace / Promptfoo evaluation | **NOT_RUN_OPTIONAL** |

The two pytest warnings are existing Starlette/httpx deprecation warnings. They did not affect any gate.

## AI and safety result

DeepSeek completed a real tool-loop smoke as `deepseek / deepseek-chat`, and the V6 flagship can use the deterministic fallback when no runtime is configured. Hermes remains separately labeled because no Hermes endpoint/key was configured. AI may act autonomously on ordinary reversible changes within the user's pre-authorized Autonomy Envelope; commitment management remains bounded by provider facts, refund/loss, schedule drift, and explicit authorization. Every predictive mutation records trigger, snapshot, inference, solver, policy, and mutation evidence.

## Required labels

```text
V5_REGRESSION = PASS
PER_JOURNEY_AUTOPILOT = PASS
COMPOSITE_PROVIDER_MESH = PASS
LIVE_OPEN_METEO = PASS
LIVE_VALHALLA = PASS
LIVE_NOMINATIM = PASS
LIVE_OVERPASS = PASS
REAL_POI_DISCOVERY = PASS
OPENFREEMAP_BASEMAP = PASS
HERMES_MODEL_BACKED = NOT_RUN_EXTERNAL
NATIVE_DEEPSEEK_MODEL_BACKED = PASS
PREDICTIVE_RESILIENCE = PASS
COUNTERFACTUAL_TWIN = PASS
PREEMPTIVE_AUTOPILOT = PASS
REAL_CITY_E2E = PASS
PHOENIX_TRACE = NOT_RUN_OPTIONAL
PROMPTFOO_EVAL = NOT_RUN_OPTIONAL
```

## Deliverables

- `reports/product-v6/FINAL_REPORT.md`
- `reports/product-v6/PROGRESS.md`
- `reports/product-v6/GATE_MATRIX.md`
- `reports/product-v6/REAL_CITY_PROVIDER_EVIDENCE.md`
- `reports/product-v6/AI_EVALUATION.md`
- `CityNexus-Predictive-Real-City-Twin-V6-Final-20260912.zip`

The ZIP is built from an explicit source staging set and excludes the temporary key, API keys, databases, `.venv`, `node_modules`, `dist`, Python caches, browser reports, and nested archives. No commit or destructive worktree cleanup was performed.
