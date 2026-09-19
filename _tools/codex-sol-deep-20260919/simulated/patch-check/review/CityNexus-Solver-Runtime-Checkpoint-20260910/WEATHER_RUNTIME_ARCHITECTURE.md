# Weather Runtime Hardening Architecture

## Authority and time model

```text
ACTIVE Journey + selected PlanVersion
-> current/future non-terminal Activities
-> explicit weather-sensitive Place scopes
-> server-owned Open-Meteo request
-> strict UTC observation arrays
-> frozen WeatherSnapshot(captured_at)
-> frozen WeatherRiskFact(snapshot_captured_at, forecast validity)
-> deterministic exact-scope/time/sensitivity attribution
-> stable PROVIDER_VERIFIED WEATHER Event
-> existing Replan pipeline at latest provider capture time
-> deterministic feasibility and C4 protection
```

Provider capture time and forecast validity are separate facts. `snapshot_captured_at` is the server observation and decision time. `forecast_valid_from` and `forecast_valid_until` describe the hourly forecast bucket. Event occurrence uses capture time so a future bucket does not advance the Journey clock.

Repeated observations of the same Journey, provider, risk code, validity bucket, Activity, Place ID, latitude, and longitude reuse the Event identity. The stored provider evidence, severity, and `snapshot_captured_at` are refreshed. Replan reads the latest capture time from trusted payload evidence when freezing its MobilitySnapshot and evaluating current recovery time.

## Coverage-aware clearing

A later successful forecast may resolve an active weather Event only when the provider response explicitly contains the same UTC forecast bucket and exact Place/coordinate scope, while no matching active risk remains. The Event becomes `RESOLVED` and stores auditable `FORECAST_CLEARED` evidence from that covered observation.

Provider failure, malformed arrays, an empty response, a missing bucket, or a different scope cannot clear an Event. Provider failure records or reuses one degradation marker and never fabricates weather.

## Existing deterministic policy

- Query once per unique eligible Place.
- `weather_sensitive` explicitly enables sensitivity.
- `indoor` is not rain-sensitive.
- `outdoor` is rain-sensitive.
- Unknown sensitivity is not auto-attributed.
- Completed, skipped, cancelled, and past execution Activities are excluded.
- Hourly intervals use half-open `[valid_from, valid_until)` overlap.
- Provider UTC instants are converted to the Journey timezone before overlap checks.
- Exact Place ID, latitude, and longitude are persisted in trusted evidence.
- The server determines `affected_activity_id`; AI does not.
- GET/Twin and deterministic gates remain network-free.
- Durable C4 Commitments remain authoritative.
