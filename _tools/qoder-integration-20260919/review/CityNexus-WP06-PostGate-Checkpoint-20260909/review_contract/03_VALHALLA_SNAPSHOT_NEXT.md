# Valhalla + MobilitySnapshot Next Phase

## Architectural rule

A live router must never execute inside the authoritative deterministic feasibility gate.

Use:

```text
Valhalla / GraphHopper / OTP
        |
        v
external provider adapter
        |
        v
capture/freeze TravelEstimateFact
        |
        v
MobilitySnapshot
        |
        v
authoritative deterministic feasibility
```

The prepared `snapshot_capture.py` provides this boundary.

## First real provider

Prefer a direct CityNexus-owned Valhalla HTTP adapter using the backend's existing `httpx` dependency. This keeps the primary provider contract under our control and avoids making a stale compatibility library mandatory.

Prepared module:

```text
backend/app/integrations/mobility/valhalla_http.py
```

It supports:

```text
/route
/sources_to_targets
```

and remains fully mock-testable using injected `httpx.Client` and place lookup.

## Optional local Python path

`pyvalhalla` can be evaluated as an optional local implementation after the HTTP adapter works. Current releases provide Windows x86-64 wheels for CPython 3.12+, which matches the project baseline.

Do not let tile-building/deployment work block the deterministic demo. If local Valhalla setup becomes expensive, keep mock/frozen mobility for the core Golden Scenario and move the live smoke test to an optional integration profile.

## Fallback semantics

If the primary router fails for a pair and an explicit safe fallback exists:

```text
primary failed
-> fallback estimate frozen
-> fact.degraded = true
-> snapshot.degraded = true
```

If neither produces a safe fact:

```text
fail explicitly
```

Never invent ETA values merely to keep the screen green.

## Integration test separation

Default CI/tests:

```text
network-free
```

Optional provider profile:

```text
CITYNEXUS_LIVE_VALHALLA_URL=...
pytest -m integration ...
```

Do not make live service availability a prerequisite for the coursework demo.
