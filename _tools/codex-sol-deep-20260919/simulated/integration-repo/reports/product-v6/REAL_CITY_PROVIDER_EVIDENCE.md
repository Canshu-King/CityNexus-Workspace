# V6 Real-City Provider Evidence

Date: 2026-09-12  
City context: Tianjin-oriented deterministic replay plus bounded live adapter smokes

## Live adapter smokes

Each smoke used a bounded request and the identified client header `CityNexus/6.0 (+https://citynexus.local/real-city)`. The Valhalla check used one fair-use route against the public development endpoint and is not a production dependency.

| Provider | Result | Evidence |
| --- | --- | --- |
| Open-Meteo | PASS | Forecast adapter received 168 hourly observations at the Tianjin replay coordinate; response normalized without inventing risk. |
| Nominatim | PASS | Bounded geocoding request returned one real relation candidate, external id `nominatim:relation/912999`. |
| Overpass | PASS | Bounded 1 km library query returned two provider-backed candidates. |
| Valhalla | PASS | Public demo route from the Tianjin replay area returned an 18-minute pedestrian estimate. |
| OpenFreeMap | PASS | Liberty style endpoint returned HTTP 200 and is used by MapLibre. |

These are provider adapter smokes, not a claim that the public services are production SLAs. The application keeps provider cache metadata, TTL, provenance, and fallback evidence so a provider outage cannot be silently treated as fresh truth.

## Replay and materialization evidence

The flagship path intentionally uses deterministic replay so the completion gate is repeatable and does not depend on public service timing. The replay mesh identifies:

- weather: `open-meteo-replay`;
- mobility: `valhalla-replay`;
- city discovery: `openstreetmap-replay`.

The replay discovery path materializes candidates such as:

- Tianjin Italian Style Town Indoor Gallery;
- Haihe Riverside Design Library;
- Tianjin Ancient Culture Street Tea House.

Each candidate retains provider key, external id, coordinates, category, tags, opening-hours evidence, captured time, expiry, and materialized `Place`/`CityService` ids. The V6 flagship test confirms that CP-SAT V2 can select a `real-place-*` replacement while keeping the protected Cruise activity.

## Failure semantics

`mode=live` is an explicit request. If live real-city providers are disabled, unavailable, malformed, or return no usable candidates, the service returns `mode=replay-fallback`, `provenance=REPLAY`, per-provider `REPLAY_FALLBACK` statuses, and a `fallback_reason`. This is deliberately distinguishable from `LIVE_PROVIDER`; it is not a false live pass.

GET projections and deterministic feasibility consume persisted observations and materialized candidates. They do not call Nominatim, Overpass, Open-Meteo, or Valhalla during projection.
