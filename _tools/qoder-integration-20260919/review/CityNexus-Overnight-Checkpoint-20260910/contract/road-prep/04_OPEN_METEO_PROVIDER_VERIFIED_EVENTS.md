# Open-Meteo Provider-Verified Event Ingestion

The checkpoint already prevents the public Event API from forging `PROVIDER_VERIFIED` provenance. Preserve that rule.

A prepared reference module exists:

`backend/app/integrations/context/weather_snapshot.py`

## Required server-side path

```text
OpenMeteoContextProvider
→ forecast()
→ risks()
→ freeze_weather_risks()
→ WeatherSnapshot
→ internal Event ingestion service
→ Event(provenance=PROVIDER_VERIFIED, provider_key=open-meteo)
```

The public browser/API client must never be allowed to submit provider-verified provenance.

## Recommended first real scenario

Use heavy rain risk against an outdoor future Activity:

```text
Open-Meteo rain probability >= threshold
→ PROVIDER_VERIFIED WEATHER Event
→ affected outdoor Activity
→ deterministic replan
→ indoor alternative if feasible
→ preserve C4
```

If Open-Meteo is unavailable:
- no provider-verified weather fact is created;
- provider status may become degraded;
- default demo can still use SIMULATED Event fixtures.

## Event lifecycle gap to close

Before live provider monitoring, define how provider outage/recovery events become `RESOLVED`. Otherwise JourneyTwin can remain DEGRADED forever after the service recovers.

Use a small internal service, not a public client-controlled status mutation.
