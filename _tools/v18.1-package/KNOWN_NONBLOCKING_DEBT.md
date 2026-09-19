# Known Non-Blocking Debt Carried Beyond Weather Freeze

These items were observed during external review. They are **not** reasons to reopen the Weather Runtime mutation batch, but they must remain visible so later work does not accidentally turn them into hidden semantics.

## 1. Resolved weather can leave a stale PRESENTED proposal visible

Observed behavior:

```text
provider-verified WEATHER Event
-> replan proposal PRESENTED
-> later successful same-bucket forecast clears the Event
-> Event = RESOLVED
-> proposal can remain PRESENTED
-> accept attempt is rejected with 409 because trigger is no longer actionable
```

Authority is safe because stale acceptance is blocked. The remaining debt is lifecycle/UI cleanup. A later proposal-retirement change may mark such proposals SUPERSEDED/RETIRED when their trigger resolves, but do not mix that work into OR-Tools V1 unless a solver test directly requires it.

## 2. Provider recovery query can be made more explicit

`resolve_provider_degradation()` is practically scoped by provider payload, but a later cleanup should explicitly filter `event_type == SERVICE_UNAVAILABLE` as defensive query hygiene.

## 3. Weather disruption is currently conservative and globally place-unavailable

After deterministic weather attribution, the current replan path maps the affected Place to the same hard `PLACE_UNAVAILABLE` rule used by closure. This is safe but conservative.

Solver V1 must preserve this meaning so the solver and authoritative feasibility gate agree.

Do **not** let OR-Tools move the same weather-hit Place outside the forecast interval unless the deterministic feasibility layer first gains an equivalent time-bounded hazard rule, for example:

```text
PLACE_RISK_INTERVAL(place_id, valid_from, valid_until, reason)
```

Only after both solver and authoritative gate understand the same rule should time-shifting a weather-sensitive Place become legal.

## 4. Weather is not yet the strongest one-minute demo story

The Closure Golden Scenario remains the best current dynamic-replanning demo. Weather is now a trustworthy context source and can identify C4/outdoor risk, but the canonical Balanced plan does not always provide a convenient flexible outdoor mid-journey replacement slot.

Later, the Explore plan or discovery layer can intentionally include a flexible outdoor activity so Weather Recovery is visually impressive without fabricating data.


