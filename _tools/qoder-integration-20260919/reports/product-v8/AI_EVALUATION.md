# AI and agent evaluation

## Native DeepSeek

Runtime label: `MODEL_BACKED_PROCESS_ONLY`. A fresh child-process smoke loaded the supplied temporary credential only into the process environment with `CITYNEXUS_AI_ENABLED=true` and `CITYNEXUS_IMPACT_PROVIDER=deepseek`. Result:

`DEEPSEEK_LIVE_SMOKE=PASS`  
`IMPACT_STATUS=VALIDATED_AI`  
`IMPACT_PROVIDER=deepseek`  
`ORT_DETERMINISTIC_GATE=PASS`

The key value was not printed, persisted, added to an audit payload, or packaged. The V8 agent UI does not expose raw model/tool JSON; it presents mission and policy progress in human terms.

## Delegated autonomy

The V8 Autopilot test verifies the intended autonomy envelope: semantic RAIN input can result in an autonomous reversible transport change when the user has authorized it and hard constraints, provider state, loss, budget, drift, and protected commitments pass. The same route under ADVISORY returns `REQUIRE_CONFIRMATION`. Learned TravelerTwin evidence remains a ranking input and never expands payment, commitment, or authority.

## Hermes, Phoenix, Promptfoo

- `HERMES_MODEL_BACKED`: `NOT_RUN_EXTERNAL`. The Hermes adapter/MCP boundary exists, but no Hermes inference endpoint and credential were configured for this local run.
- `PHOENIX_TRACE`: `PASS_LOCAL_OPTIONAL_EXPORTER` for the existing local OpenInference-shaped trace persistence; no external Phoenix export is claimed.
- `PROMPTFOO_EVAL`: `PASS_LOCAL_DETERMINISTIC_ADAPTER` based on the preserved V7 13/13 local adversarial evaluation. The npm Promptfoo model-backed CLI is not claimed as run in V8.

