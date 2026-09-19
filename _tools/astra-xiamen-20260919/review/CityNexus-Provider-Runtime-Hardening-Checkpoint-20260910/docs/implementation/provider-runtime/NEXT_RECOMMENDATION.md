# Next Recommendation

Proceed with **Open-Meteo runtime weather-to-Activity mapping before OR-Tools**.

The mobility runtime now establishes the reusable provider pattern: external
facts are normalized, frozen, attributed and then consumed by deterministic
logic. The next product-value gap is turning weather observations into a
deterministically affected Journey Activity and a `PROVIDER_VERIFIED` Event.

Recommended next chain:

```text
Open-Meteo
-> WeatherRiskFact / WeatherSnapshot
-> deterministic time + location intersection with Activity
-> affected_activity_id
-> PROVIDER_VERIFIED Event
-> existing Replan pipeline
```

OR-Tools should follow that gate. It can improve candidate generation, but it
does not add a new reality source, and it must continue to submit candidates to
the same deterministic feasibility/C4 protection boundary.
