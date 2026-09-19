# Next Gate - Open-Meteo Runtime Weather -> Activity

Start this **only after Provider Runtime is FROZEN_PASS**.

## Existing foundation already present

The repository already contains:

- `OpenMeteoContextProvider`;
- Unix timestamp / UTC-safe parsing;
- `WeatherObservation` and `WeatherRisk`;
- `WeatherSnapshot` / `WeatherRiskFact`;
- `freeze_weather_risks()`;
- server-owned `PROVIDER_VERIFIED` event ingestion;
- provider degradation and recovery helpers.

The missing product-runtime capability is deterministic attribution:

```text
Open-Meteo fact
-> which Journey Activity does it actually affect?
```

Today `affected_activity_id` can still be supplied manually to the internal
weather ingestion helper.

## Recommended authority chain

```text
Upcoming/current Journey Activities
-> determine explicit weather-query scope/location
-> Open-Meteo call OUTSIDE domain gate
-> normalize UTC observations
-> freeze WeatherSnapshot
-> deterministic time/location/weather-sensitivity matcher
-> affected_activity_id
-> server-owned PROVIDER_VERIFIED Event
-> existing Replan pipeline
```

AI must not choose the affected Activity.

## Design questions Codex should resolve from the real repo

1. Query per unique upcoming Place, or use an explicit city-wide weather scope?
2. How is weather sensitivity represented?
   - explicit `indoor`/`outdoor` tags;
   - explicit metadata flag;
   - documented deterministic category policy.
3. What time window makes an hourly weather risk apply to an Activity?
4. How are duplicate provider observations/events deduplicated?
5. How is provider query location/scope persisted in evidence?
6. How does a weather risk affecting a C4 Commitment get represented without
   auto-deleting that commitment?

Prefer the smallest explicit policy over clever inference.

## Proposed Weather Runtime acceptance tests

### WRT-01 - Real Open-Meteo contract via `httpx.MockTransport`

Unix UTC response -> parsed observations -> risk -> frozen snapshot.

### WRT-02 - Timezone-safe mapping

A UTC risk instant maps to the Journey timezone before Activity overlap is
checked.

### WRT-03 - Deterministic time intersection

A risk outside an Activity's applicability window must not target it.

### WRT-04 - Deterministic location/scope attribution

A risk must carry enough query location/scope evidence to prove why it applies
to the selected Activity.

### WRT-05 - Indoor/outdoor policy

Heavy rain must not target a clearly indoor Activity merely because the time
overlaps. A clearly weather-sensitive/outdoor Activity should be eligible.

### WRT-06 - Execution-state filter

Completed/skipped/cancelled activities must not become new weather targets.
Current/upcoming activities may.

### WRT-07 - Provider-verified provenance is server-owned

The public Event API still cannot forge `PROVIDER_VERIFIED` provenance.

### WRT-08 - Idempotent provider event ingestion

The same provider risk fact for the same Journey/Activity/time should not create
unbounded duplicate Events on repeated polling.

### WRT-09 - Provider failure creates degradation, not fake weather

Open-Meteo failure -> explicit provider degradation evidence / Twin DEGRADED;
no invented rain Event.

### WRT-10 - Recovery closes degradation state

Provider recovery resolves its degradation event and Twin can return READY.

### WRT-11 - C4 safety

If weather affects a C4 Activity, event attribution may identify it, but
replanning must not silently remove or rewrite the durable commitment.

### WRT-12 - Offline Golden regression

The existing Closure Golden Scenario remains fully operational with Open-Meteo
disabled/unavailable.

## Hard stop

When WRT-01..WRT-12 and the old Provider/Golden gates pass, stop and package a
review checkpoint. OR-Tools comes after this gate.
