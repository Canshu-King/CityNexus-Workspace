# CityNexus Weather Runtime Checkpoint

Date: 2026-09-10

Weather Runtime Gate = **FROZEN_PASS** locally.

The smallest server-owned path is now implemented:

`current/future Activities -> explicit outdoor or weather_sensitive Place scopes -> Open-Meteo outside the deterministic gate -> UTC-normalized frozen WeatherSnapshot/WeatherRiskFact -> deterministic scope, time and sensitivity attribution -> server-owned PROVIDER_VERIFIED Event -> existing Replan pipeline`

The trigger is an explicit server-owned `POST /api/v1/journeys/{journey_id}/weather/refresh` operation. It accepts no request body or trusted weather facts. The server owns the provider call and evidence creation. No scheduler or background worker was introduced because the real repository has no existing scheduling foundation.

The implementation queries one time per unique eligible Place. Only current and future non-terminal Activities are eligible. `indoor` is protected from rain attribution, `outdoor` is rain-sensitive, `weather_sensitive` is an explicit override, and unknown Places are not auto-attributed.

Provider timestamps and snapshot capture timestamps are normalized to UTC. Hourly risks use the half-open interval `[valid_from, valid_until)`. Attribution requires the exact Place ID and coordinates recorded in the query scope, then converts the interval into the Journey timezone before checking overlap.

Repeated identical weather polling reuses the existing Event. Repeated outages reuse one unresolved degradation marker. Recovery resolves degradation only when every attempted scope in the refresh succeeds. Provider failure never creates a fake weather Event.

Weather may identify a durable C4 Activity, but existing Replan safeguards reject unsafe removal and leave the C4 Commitment authoritative.

GET/Twin and deterministic feasibility paths do not call Open-Meteo. AI does not choose `affected_activity_id`.

No OR-Tools work was started in this mutation batch.
