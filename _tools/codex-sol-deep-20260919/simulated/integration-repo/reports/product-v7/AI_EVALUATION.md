# V7 AI Evaluation and Runtime Evidence

## Adversarial evaluation

`evals/promptfoo/run_local.py` executed the CityNexus delegation-policy adapter with **13/13 PASS**. The cases cover:

- prompt injection in city-event text;
- hallucinated POI and unverified coordinates;
- unknown opening hours;
- budget widening;
- protected C4 Commitment mutation;
- duplicate requests;
- invalid Activity IDs;
- stale provider evidence;
- explicit-vs-learned conflict;
- low-risk preemptive action;
- spoofed user confirmation;
- exhausted tool loops.

Runtime label: `LOCAL_DETERMINISTIC_ADAPTER`; this is a server-policy evaluation, not a model-backed Promptfoo score. The API key is not referenced by the config or output. The literal npm Promptfoo command was attempted and could not finish because the C: drive reported `ENOSPC`; the local adapter provides the reproducible result without installing another package.

## Native DeepSeek smoke

A real OpenAI-compatible DeepSeek tool-calling loop completed in this iteration with `provider=deepseek`, status `COMPLETED`, and no failure reason. The persisted tool trace selected `inspect_journey`, `inspect_twin`, `list_replans`, `request_replan`, and `search_city_services`. The run carried a persisted trace ID and the observability endpoint returned `deepseek.call`, `agent.tool_call`, `real_city.discovery`, `cp_sat.solve`, and `mission.compile` spans.

## Hermes boundary

The official Hermes Windows installer was attempted in an isolated directory. Its local prerequisite stages completed, but the GitHub repository clone failed due external connectivity. Therefore `HERMES_MODEL_BACKED` is explicitly `PARTIAL_NOT_RUN_EXTERNAL`; the native DeepSeek runtime is the verified fallback. The checked-in MCP V2 server and Gateway remain server-owned and do not expose shell, file, browser, payment-capture, refund, or raw database capabilities.

## Autonomy interpretation

The policy does not treat an LLM-originated judgment as automatically read-only. Reversible ordinary actions inside the user's Autonomy Envelope may execute autonomously after server validation. Deterministic feasibility validates the post-action Journey and business facts; it does not attempt to replace semantic interpretation of unstructured city events. Budget, loss, booking type, provider state, protected Commitment, and schedule-drift gates remain authoritative.
