# Weather Runtime Architecture

## Authority chain

```text
Journey ACTIVE/selected PlanVersion
-> current + future Activities
-> explicit weather-sensitive Place scope
-> Open-Meteo call outside domain gate
-> normalize UTC provider observations
-> freeze WeatherSnapshot / WeatherRiskFact
-> deterministic time + exact scope + sensitivity attribution
-> server-owned PROVIDER_VERIFIED Event
-> existing Replan pipeline
-> deterministic feasibility + C4 protection
```

The server, rather than AI, determines `affected_activity_id`.

## Trigger and read safety

The MVP trigger is `POST /api/v1/journeys/{journey_id}/weather/refresh`. The operation accepts no request body. It creates its own Open-Meteo client and freezes provider evidence before Event ingestion.

`GET /twin`, feasibility evaluation, replan candidate generation, and other read or projection paths do not call Open-Meteo.

## Deterministic policy

- Query once per unique eligible Place.
- `weather_sensitive` is an explicit override.
- `indoor` is not rain-sensitive.
- `outdoor` is rain-sensitive.
- Unknown sensitivity is not auto-attributed.
- Completed, skipped, and cancelled Activities are excluded.
- Activities before the current execution position are excluded.
- Weather intervals use half-open `[valid_from, valid_until)` overlap.
- Provider instants and captured evidence are normalized to UTC before Journey timezone comparison.
- Exact Place ID, latitude, and longitude are persisted in the query scope.

Provider failure creates provider-state evidence only. C4 Commitments remain durable authority.
