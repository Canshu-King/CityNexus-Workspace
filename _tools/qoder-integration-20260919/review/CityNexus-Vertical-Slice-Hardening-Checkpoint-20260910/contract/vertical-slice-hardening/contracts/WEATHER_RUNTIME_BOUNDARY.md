# Weather Runtime Boundary - Prepared Follow-up

This is a future bounded contract, not part of the current hardening merge.

## Existing good pieces

CityNexus already has:

- Open-Meteo HTTP parsing
- UTC/Unix timestamp handling
- frozen weather risk facts
- server-owned `PROVIDER_VERIFIED` weather Event ingestion
- provider degradation/recovery Event support

## Remaining product-runtime gap

A weather provider observation is not automatically a Journey disruption.

`ingest_provider_verified_weather_event` accepts an optional `affected_activity_id`. If runtime ingestion creates a weather Event without mapping the risk to Journey time/place/activity, replan cannot reliably know which Activity is disrupted and may produce only a stable/no-op plan.

## Correct boundary

```text
Open-Meteo forecast
-> normalize absolute observations
-> freeze WeatherRiskFact
-> intersect fact time/location with Journey active/upcoming activities
-> derive affected interval/activity with deterministic rules
-> persist PROVIDER_VERIFIED Event
-> replan
```

AI must not decide whether rain invalidates a hard activity constraint.

## Minimum future tests

- UTC risk at 05:25Z maps to a +08 Journey activity at 13:25.
- Risk outside Journey interval does not create an affected Journey Event.
- Risk affecting an indoor/compatible service obeys deterministic policy rather than always forcing replan.
- Open-Meteo unavailable creates provider degradation, not fake weather.
- Recovery resolves provider degradation without rewriting past weather facts.
