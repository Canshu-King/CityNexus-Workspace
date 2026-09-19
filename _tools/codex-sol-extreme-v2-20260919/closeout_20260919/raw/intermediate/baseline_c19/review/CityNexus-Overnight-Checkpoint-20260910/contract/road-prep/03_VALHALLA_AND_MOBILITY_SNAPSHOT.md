# Valhalla + MobilitySnapshot Next Step

The checkpoint already has a good architectural boundary:

```text
Valhalla HTTP
→ parse/validate provider response
→ TravelEstimateFact
→ MobilitySnapshot
→ deterministic feasibility/replanning
```

Do not pass a live HTTP provider object directly into the gate.

## Next implementation

1. Keep `ValhallaHTTPMobilityProvider` optional and injectable.
2. Add one controlled smoke profile using `CITYNEXUS_LIVE_VALHALLA_URL` only when explicitly enabled.
3. Capture all plan-adjacent travel pairs needed for a candidate before gate execution.
4. Freeze them with `capture_mobility_snapshot()`.
5. Put provider provenance and degraded/fallback information into Replan evidence and JourneyTwin context.
6. If Valhalla fails:
   - use explicit deterministic fallback only if configured;
   - mark snapshot degraded;
   - never fabricate travel facts.

## Matrix optimization

For many candidates, prefer Valhalla matrix calls over repeated route calls. A candidate generator often needs N×N ETA facts; this is where a matrix endpoint actually saves time rather than looking impressive in an architecture diagram.

## Map geometry

Route shape belongs to frontend visualization evidence, not feasibility authority. Store/fetch route geometry separately from the minute facts used by the gate.

## GraphHopper / OTP

- GraphHopper remains an optional second road/walk/bike implementation.
- OpenTripPlanner is a Transit provider only when usable GTFS/GTFS-RT data exists.
- Do not force either into the MVP default path.
