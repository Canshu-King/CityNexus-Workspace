# DeepSeek through LiteLLM

## Goal

Use DeepSeek as the first real AI provider without hard-coding CityNexus to one model vendor.

```text
CityNexus AIProvider
        |
        v
     LiteLLM
        |
        +-- DeepSeek (primary config)
        +-- other provider later if needed
```

## Environment contract

```text
CITYNEXUS_AI_ENABLED=false
CITYNEXUS_AI_PROVIDER=litellm
CITYNEXUS_AI_MODEL=<configured LiteLLM DeepSeek model string>
DEEPSEEK_API_KEY=<backend secret only>
```

Do not hard-code a model name in domain/application code. Models change faster than coursework requirements, because apparently even software needs weather.

## First WP07 use case

`explain_replan(diff, verified_facts)` only.

The first real model integration should not parse/mutate the entire Journey. It should receive:
- ReplanDiff;
- protected commitments;
- verified travel/cost deltas;
- reason codes;
- provider degraded indicators.

If LiteLLM/DeepSeek fails, deterministic fallback text is returned and the same replan remains usable.

## Later use cases

- free-text preference parsing -> proposed structured preferences -> deterministic validation;
- recommendation explanation;
- Copilot read-only questions;
- PydanticAI tool calling only after these are stable.
