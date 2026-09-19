# CityNexus Autonomous City Intelligence V3 Final Report

Date: 2026-09-11

## Outcome

The V3 product slice is implemented in the current CityNexus repository. The
flagship path now connects a natural-language mission to a server-owned
Journey Mission, a real DeepSeek model-backed tool loop, MCP V2-compatible
Gateway actions, impact intelligence, Place-backed alternatives, deterministic
feasibility, Solver V2 candidates, persisted AgentRun history, and the
Control Tower UI.

The capability boundary is explicit: the workspace verified the CityNexus
DeepSeek adapter and MCP protocol surface, but did not claim Hermes CLI
execution because no Hermes binary/provider runtime was installed.

## Architecture delivered

```text
user mission
  -> JourneyMission + bounded Autonomy Envelope
  -> DeepSeek semantic interpretation
  -> AgentRun / model-selected Gateway tool loop
  -> MCP V2-compatible inspect / plan / action surface
  -> ImpactAssessment + primary/secondary risk evidence
  -> Place-backed alternatives and Solver V2 Top-K
  -> deterministic CityNexus feasibility/business-fact gate
  -> policy decision / typed mutation / approval receipt when required
  -> JourneyTwin, MapLibre route/scope, Feed, persisted reload
```

The deterministic layer verifies the post-action Journey: schedule overlap,
travel feasibility from a frozen snapshot, opening windows, budget, provider
facts, protected commitments, and business state. It does not attempt to
replace valid LLM semantic judgment about ordinary unstructured city events.

## Gate disposition

| Gate family | Disposition | Notes |
| --- | --- | --- |
| AIV3-01..03 | FROZEN_PASS | Step-up proof class is distinct from USER_CONFIRMATION and a method label. |
| LIVE-01..07 | MODEL_BACKED / PROTOCOL_VERIFIED | DeepSeek model-backed CityNexus loop passed; MCP V2 protocol passed; Hermes CLI remains external. |
| MIS-01..05 | E2E_VERIFIED | Mission authority is compiled, bounded by policy, persisted, enforced, and reloadable. |
| IMP3-01..06 | FROZEN_PASS | Fuzzy/geospatial/temporal evidence, primary + secondary risks, protected risk-only behavior. |
| ALT-01..05 | E2E_VERIFIED | Search, server Place materialization, deterministic gate, low-risk autonomous replacement. |
| SOL2-01..07 | INTEGRATED | Multi-slot deterministic Top-K through the existing replan contract; V1 is preserved. |
| UI-01..06 | E2E_VERIFIED | Command center, live persisted trace, map scope/risk, before/after route, reload. |
| E2E-01 | PARTIAL / HONEST | Backend DeepSeek + MCP-compatible end-to-end path passed; literal Hermes CLI execution was unavailable. |

## Verification record

The final counts are recorded in `TEST_RESULTS.md` and were rerun after the
Solver V2 integration. The final checkpoint replay also repeats the artifact
exclusion and secret scans.

- backend full pytest: see `TEST_RESULTS.md`;
- focused V3 / Solver V2 tests: see `TEST_RESULTS.md`;
- MCP V1/V2 unit and stdio protocol discovery;
- OpenAPI formal/runtime parity;
- compileall and Ruff;
- frontend build and Playwright Control Tower suite;
- real DeepSeek model-backed smoke with transient credential handling.

## Security and audit boundaries

- raw Event truth remains separate from model-derived ImpactAssessment;
- AI-selected IDs are resolved against server-owned Journey/Place facts;
- ordinary reversible in-envelope changes may auto-execute in Autonomous mode;
- durable Commitment changes require explicit authority and policy/provider/loss conditions;
- high-risk Gateway tools remain callable by the Agent but return the policy decision;
- model output and chain-of-thought are not persisted; tool arguments/results and decisions are;
- the final package excludes credentials, runtime databases, environments,
  dependencies, caches, and browser artifacts.

## Remaining external or optional work

- install/configure and separately verify the Hermes CLI provider runtime;
- configure live Valhalla for provider-backed route-shape replay;
- replace the demo step-up verifier with production identity/WebAuthn;
- optional Phoenix/Promptfoo observability/evaluation polish;
- split the large MapLibre frontend chunk if initial-load performance requires it.
