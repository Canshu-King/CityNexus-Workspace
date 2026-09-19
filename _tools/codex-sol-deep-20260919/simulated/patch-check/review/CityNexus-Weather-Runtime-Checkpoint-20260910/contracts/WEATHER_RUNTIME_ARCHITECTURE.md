# Weather Runtime Architecture Contract

## Authority chain

```text
Journey ACTIVE/selected PlanVersion
-> current + future Activities
-> explicit weather-sensitive Place scope
-> Open-Meteo call outside domain gate
-> normalize UTC provider observations
-> freeze WeatherSnapshot / WeatherRiskFact
-> deterministic time + scope + sensitivity attribution
-> server-owned PROVIDER_VERIFIED Event
-> existing Replan pipeline
-> deterministic feasibility + C4 protection
```

AI does not choose `affected_activity_id`.

## Query policy

For the current MVP, query once per unique eligible Place. This is intentionally simple and auditable. A future optimization can cluster nearby Places, but only if scope evidence remains explicit.

## Sensitivity policy

Use explicit Place tags only:

```text
weather_sensitive -> eligible override
indoor             -> not rain-sensitive
outdoor            -> rain-sensitive
unknown            -> do not auto-attribute
```

Do not infer from free-form titles or ask an LLM.

## Time policy

Treat an hourly provider risk as a half-open validity interval:

```text
[risk_at, risk_at + 60 minutes)
```

Convert provider UTC instants to the Journey timezone before comparing against Activity schedule intervals.

Half-open overlap rule:

```text
max(risk_start, activity_start) < min(risk_end, activity_end)
```

## Execution policy

Never create new weather targets for terminal Activities:

- COMPLETED
- SKIPPED
- CANCELLED

When `Journey.current_activity_id` is known, only current/future sequence numbers are eligible.

## Provenance policy

A trusted Event must preserve enough evidence to answer:

- which provider?
- which query Place?
- exact latitude/longitude?
- provider forecast validity interval?
- risk reason code?
- provider measurements?
- which Activity was selected?
- why was it selected?

## Deduplication policy

The same tuple must not create unlimited duplicate Events:

```text
journey
+ provider
+ risk code
+ validity start/end
+ affected Activity
+ query scope Place
```

No file/hash review is required. This is business idempotency, not archive hashing.

## Degradation policy

Provider failure must produce provider-state evidence only. It must not invent a weather observation.

Repeated failures should reuse one unresolved degradation marker. Recovery may resolve the marker only after a successful provider operation for all scopes attempted by that refresh.

## C4 policy

Weather attribution is allowed to identify a C4 Activity. It is not allowed to remove, unlock, rewrite, or silently relocate the durable C4 Commitment.

A conservative replan rejection is acceptable until a richer C4-aware weather recovery family exists.

## Read safety

`GET JourneyTwin`, list Events, and other read/projection paths must never perform live Open-Meteo calls.
