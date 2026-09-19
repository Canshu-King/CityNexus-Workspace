# AI boundary: verified facts first, natural language second

## Required pipeline

```text
Deterministic facts
  -> ReasonCodes + Evidence
  -> AIProvider
  -> natural-language explanation
```

Example verified payload:

```json
{
  "reason_codes": [
    "INTEREST_MATCH",
    "WITHIN_OPPORTUNITY_WINDOW",
    "OPEN_AT_VISIT_TIME",
    "LOW_DETOUR",
    "BUDGET_FIT",
    "NEXT_COMMITMENT_SAFE"
  ],
  "evidence": {
    "walk_minutes": 8,
    "visit_minutes": 45,
    "safety_buffer_minutes": 22,
    "cost_minor": 0
  }
}
```

DeepSeek/LiteLLM may turn this into a friendly sentence, but must not invent evidence.

## Initial AI scope

- preference parsing into a proposal that is revalidated by deterministic code;
- place recommendation explanation from verified candidates;
- replan explanation from `ReplanDiff`;
- Copilot answers against current JourneyTwin facts.

## Explicitly forbidden

- hard constraint pass/fail;
- opening/availability truth;
- ETA truth;
- payment truth;
- C4/strength promotion;
- plan activation;
- direct mutation without a deterministic application-service gate.
