# LiteLLM + DeepSeek Journey Copilot

Use AI after deterministic WP06 evidence is stable.

Prepared safety contract:

`backend/app/integrations/ai/copilot_contract.py`

## AI may do

- parse free-text preferences into a proposed structured request;
- explain why a verified plan/replan was chosen;
- explain Commitment/C4 using stored facts;
- summarize ReplanDiff and FeasibilityEnvelope;
- recommend real candidate Places supplied by City Discovery;
- propose a user action such as `REQUEST_REPLAN`.

## AI may not do

- declare hard feasibility;
- invent ETA/opening hours/provider status;
- mark payment successful;
- create C4 truth;
- mutate Journey/Plan/Booking/Payment directly;
- claim a real provider fact when only mock/simulated evidence exists.

## Provider structure

```text
ResilientAIExplanationService
├─ primary: LiteLLM / DeepSeek
└─ fallback: DeterministicFallbackAIProvider
```

Use environment configuration only. Never put API keys in frontend code or checkpoint packages.

## First production-worthy AI endpoint

Start with **replan explanation**, not an autonomous chat agent. It has the cleanest verified input:

```text
ReplanDiff
+ score breakdown
+ FeasibilityEnvelope
+ protected commitments
+ provider degradation
→ natural-language explanation
```

Then add Journey Copilot tool-calling after read-only tool contracts are stable.
