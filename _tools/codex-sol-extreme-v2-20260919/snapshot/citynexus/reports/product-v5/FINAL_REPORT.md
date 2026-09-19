# CityNexus Live Journey Autopilot V5 — Final Report

Date: 2026-09-12  
Repository: `D:\moodle\CityNexus`

## Outcome

**LIVE JOURNEY AUTOPILOT V5 is complete.** The required completion gate is green: a browser can start a Journey, set a standing autonomous mission, start the server-owned Autopilot, transition a provider fixture from normal to disrupted, and receive an automatic recovery without a new chat prompt or a manual Guardian scan. The recovery uses CP-SAT Solver V2, passes the Delegation Policy, mutates the active Plan, preserves protected Cruise/Dinner/C4 commitments, streams persisted operations, updates route evidence, survives reload, and suppresses the repeated incident.

The final artifact is:

`CityNexus-Live-Journey-Autopilot-V5-Final-20260912.zip`

## Architecture delivered

```text
provider refresh / demo fixture
        -> server-owned observations and semantic incident fingerprint
        -> Guardian pulse worker and cooldown/dedup
        -> configured Hermes or native DeepSeek runtime
        -> CityNexus MCP/Gateway tools
        -> CP-SAT Solver V2 remaining-horizon feasibility
        -> Delegation Policy and Autonomy Envelope
        -> Plan/Booking/Commitment-safe domain mutation
        -> Audit/SSE/Control Tower/JourneyTwin/MapLibre
```

The deterministic layer validates the post-action Journey against hard constraints and business facts. It does not attempt to replace the model's semantic judgment about an unstructured city event. Server grounding, ownership, current state, provider readiness, reversibility, money/loss limits, protected commitments, and the user's pre-authorized envelope remain authoritative.

## External findings and fixes

All seven external V4 findings were verified against the current workspace. The three supplied Mission Authority failures were reproduced before implementation and now pass. The final fixes are summarized in [PROGRESS.md](PROGRESS.md), with individual evidence in [GATE_MATRIX.md](GATE_MATRIX.md).

Notable product corrections:

- Guardian now uses the configured Agent runtime as the primary path and retains the former deterministic controller as an offline fallback.
- Provider changes are ingested by a server-owned signal/pulse layer; the flagship browser test does not create Events or call `/guardian/scan`.
- Cooldown and dedup operate on semantic incident identity rather than raw Event IDs.
- Mission authority is monotonic: model semantics can clarify ambiguity but cannot enlarge explicit caps, erase explicit protection, or grant authority to unresolved references.
- The final package is built from an explicit source staging set and scanned for the V4 hygiene failure modes.

## Validation results

| Check | Result |
| --- | --- |
| Supplied V5 Mission Authority tests | 3 passed |
| Focused V5/contract/Guardian/Solver/Mission gates | 13 passed |
| Full backend pytest | **320 passed, 2 skipped, 2 warnings** |
| Ruff lint | passed |
| Ruff format check | passed |
| Python compileall | passed |
| Frontend production build | passed |
| Full Playwright suite | **6 passed** |
| Native DeepSeek live smoke | passed |
| Deterministic runtime fallback | passed |
| Archive hygiene and fresh-extract replay | passed |

The native DeepSeek smoke used the supplied temporary key only in the child process. It was not copied into source, reports, or the final ZIP. The resulting persisted AgentRun was `provider_key=deepseek`, `model_key=deepseek-chat`, `status=COMPLETED`, with model-selected tool trace:

`inspect_journey → inspect_twin → list_replans → search_city_services → request_replan → list_replans → accept_replan`

Hermes was not claimed as live-backed because no Hermes endpoint/key was configured. The deterministic fallback evidence is separately recorded as `citynexus-guardian / deterministic-recovery-controller-v1`.

## Final labels

```text
MISSION_AUTHORITY_MONOTONIC = PASS
CITY_SIGNAL_PIPELINE = PASS
GUARDIAN_AUTORUN = PASS
GUARDIAN_MODEL_ORCHESTRATED = PASS
HERMES_MODEL_BACKED = NOT_RUN_EXTERNAL
NATIVE_DEEPSEEK_MODEL_BACKED = PASS
ORTOOLS_CP_SAT_V2 = PASS
ZERO_TOUCH_GUARDIAN_E2E = PASS
LIVE_VALHALLA = NOT_RUN_EXTERNAL
PHOENIX = NOT_RUN_OPTIONAL
PROMPTFOO = NOT_RUN_OPTIONAL
```

The optional labels are intentionally not conflated with the V5 completion gate. The flagship zero-touch autonomous recovery is the shipped milestone and is green.
