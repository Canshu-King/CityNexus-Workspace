# V6 AI Evaluation and Authority Report

Date: 2026-09-12

## Model/runtime results

### Native DeepSeek

PASS. A process-only credential smoke completed a native Agent runtime run with:

`provider_key=deepseek`  
`model_key=deepseek-chat`  
`status=COMPLETED`

The model-backed tool trace was:

`inspect_journey → inspect_twin → list_replans → request_replan → list_replans → accept_replan`

A separate DeepSeek impact smoke also returned `VALIDATED_AI` while the deterministic post-action gate remained PASS. The temporary credential was never printed or persisted.

### Hermes

NOT_RUN_EXTERNAL. The repository contains a Hermes adapter and configured-runtime routing, but no Hermes endpoint/key was available in the workspace. The native DeepSeek trace is not relabeled as Hermes.

### Offline fallback

PASS. When a model runtime is unavailable, the deterministic Guardian controller remains available and is recorded as a fallback with its own provider/model identity. This preserves the offline Golden and V5 zero-touch path without claiming model-backed execution.

## Authority semantics

The V6 implementation follows the supplied autonomy direction:

- DeepSeek may interpret ambiguous, unstructured city events and user intent.
- Hermes/DeepSeek tool requests pass through the CityNexus Gateway and Delegation Policy.
- CP-SAT V2 and the deterministic layer verify the post-action Journey: schedule, budget, provider state, ownership, feasibility, commitment preservation, and loss/drift bounds.
- Ordinary reversible in-envelope Activity changes can be `ALLOW_AUTO` even when the semantic trigger is model-derived.
- Durable commitments are protected by authorization, provider state, refund/loss facts, and the Autonomy Envelope; C4 is not an unconditional AI ban.
- A high-risk capability can be exposed through the Gateway and return `REQUIRE_CONFIRMATION`, `REQUIRE_STEP_UP`, or `DENY` rather than disappearing from the tool surface.

## Predictive evaluation

The flagship scenario records:

1. provider forecast before hard failure;
2. deterministic `PREDICTIVE_WEAKNESS` resilience status;
3. bounded counterfactuals with no Domain Truth mutation;
4. real-city candidate discovery/materialization;
5. CP-SAT V2 replacement selection;
6. policy `ALLOW_AUTO`;
7. preemptive `EXECUTED` mutation;
8. protected Cruise/C4 preservation;
9. persistent Plan/Guardian/Control Tower evidence after reload.

The repeated pulse returns the original predictive Guardian run as deduplicated. It does not create another PlanVersion or repeatedly spend the autonomy budget.

## Optional evaluation boundaries

Phoenix/OpenInference tracing and Promptfoo adversarial suites were not configured, so they remain `NOT_RUN_OPTIONAL`. No result is promoted to PASS by inference.
