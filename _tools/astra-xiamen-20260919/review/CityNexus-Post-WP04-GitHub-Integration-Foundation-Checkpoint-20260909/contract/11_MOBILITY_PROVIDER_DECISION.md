# Mobility provider decision for the current Windows/Python project

## Default engineering order

1. `routingpy` becomes the CityNexus mobility client abstraction.
2. Valhalla is the first real routing target.
3. GraphHopper is the second comparison/provider option.
4. OpenTripPlanner is reserved for real transit when a usable GTFS feed is confirmed.

## Why Valhalla first

The current Valhalla project publishes `pyvalhalla` binary wheels for `win-amd64` and Python >=3.12, which matches the current CityNexus backend target. It also covers route, matrix, isochrone and map-matching/tour capabilities.

CityNexus should still prefer the `routingpy` boundary rather than binding all domain code directly to pyvalhalla. A direct pyvalhalla experiment is useful if starting a local HTTP service becomes inconvenient.

## Why GraphHopper second

GraphHopper remains excellent and supports route, isochrone, map matching, GTFS/public transit and many profiles, but the current open-source quick start requires a modern Java runtime (current repo documentation uses Java 25). That is a larger runtime addition than the Python-first Valhalla experiment.

## Why OTP later

Current OTP2 requires Java 25+ and is data-heavy. Its value becomes high only when CityNexus has a usable OSM + GTFS dataset. It should answer transit/multimodal travel questions, not replace the CityNexus planner.

## Required CityNexus API shape

```text
MobilityProvider
  estimate(origin, destination, departure_time, mode)
  matrix(locations, departure_time, mode)
  optional route geometry
  provider status/degraded state
```

The existing `estimate_minutes(origin_place_id, destination_place_id)` remains as a compatibility shim until WP06 migrates callers.
