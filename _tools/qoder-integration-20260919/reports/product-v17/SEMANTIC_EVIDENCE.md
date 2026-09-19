# V17 Semantic Evidence

## Contract

`backend/app/integrations/ai/semantic_compiler.py` validates the exact
top-level envelope required by the V17 contract. Unknown top-level fields,
invalid enum values, invalid confidence, malformed entities, and malformed
constraints are rejected.

DeepSeek is called with the CityNexus JSON Schema and the response is parsed
once. The verified context contains only bounded Journey, selected-plan,
current-activity, preferences, and protected-commitment facts.

## Authority boundary

`apply_semantic_policy` maps meaning to an existing server route. A valid
model envelope is not replaced by the old fallback classifier. The server
still decides whether an Event may be created and never accepts model-only
coordinates, prices, provider status, IDs, commitments, or mutations.

Assertions that remain non-events:

- hypothetical requests are read-only What-If;
- unverified claims route to evidence verification;
- negated and historical statements do not create live Events;
- personal emergencies route to personal assistance.

Asserted current and asserted future city disruptions are eligible for the
existing recovery path, with `effective_time` preserved in Event evidence.

## Focused evidence

- `tests/test_v17_semantic_compiler.py`: **8 passed**;
- `tests/test_v16_integration.py` and `tests/test_v15_copilot.py`: **16 passed**;
- the full backend regression: **417 passed, 2 skipped, 2 warnings**;
- one live DeepSeek semantic canary: **SKIPPED — no configured credential**.

The warnings are existing FastAPI/Starlette/httpx dependency deprecations.
