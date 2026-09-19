# Real provider integration without weakening deterministic feasibility

## Problem

Current feasibility correctly refuses arbitrary live providers. A live network call inside the hard gate would make the same candidate pass/fail depending on timing, outage, retry or provider drift.

## Required pattern

```text
routingpy / Valhalla / GraphHopper / OTP
            |
            v
external call + timeout/retry policy
            |
            v
verified response parsing
            |
            v
TravelEstimateFact[]
            |
            v
MobilitySnapshot (frozen)
            |
            v
Authoritative deterministic feasibility
```

The prepared `provider_snapshots.py` reference implements this boundary.

## Snapshot evidence

Each fact should carry at least:

- origin semantic key;
- destination semantic key;
- minutes;
- source provider key;
- captured_at;
- degraded/fallback indicator.

Later extensions may add:

- distance;
- geometry/polyline;
- mode;
- provider response reference;
- validity horizon.

## Provider failure policy

If a real provider fails:

1. use a deterministic cached/mock snapshot if policy allows;
2. mark Twin/Envelope degraded;
3. never invent ETA using AI;
4. if no safe mobility fact exists, return explicit unavailable/infeasible result.

## Integration order

1. keep MockMobilityProvider as baseline;
2. install/use `routingpy` behind the existing adapter;
3. Valhalla first;
4. Open-Meteo context next;
5. GraphHopper alternate provider;
6. OTP only after usable GTFS is confirmed.
