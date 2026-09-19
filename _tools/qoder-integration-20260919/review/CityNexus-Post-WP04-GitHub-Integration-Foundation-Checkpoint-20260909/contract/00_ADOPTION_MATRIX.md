# GitHub adoption matrix

The rule is **use the useful capability, not the repository's entire architecture**.

| Project | Decision | CityNexus role | Earliest gate | Runtime? |
|---|---|---|---|---|
| `maplibre/maplibre-gl-js` | ADOPT | map rendering, POI, route, event and before/after replan layers | WP08 foundation may start after WP05 API stabilises | yes, frontend |
| `Turfjs/turf` | ADOPT | client-side GeoJSON bounds, distance, buffers, route fitting | WP08 | yes, frontend |
| `routingpy/routingpy` | ADOPT | one Python mobility client surface | WP06 real-provider branch | yes, backend |
| `valhalla/valhalla` | ADOPT PROVIDER | default self-hostable road/walk/bike route + matrix + isochrone | after WP06 mock core passes | optional service |
| `graphhopper/graphhopper` | ADOPT PROVIDER | alternative road routing / map matching / comparison provider | after Valhalla adapter | optional service |
| `opentripplanner/OpenTripPlanner` | ADOPT TRANSIT PROVIDER | scheduled transit + GTFS/OSM multimodal mobility | only when a usable GTFS feed is available | optional service |
| `google/or-tools` | ADOPT | advanced deterministic planner/replanner optimization | after WP06 deterministic baseline passes | yes, Python optional dep |
| `BerriAI/litellm` | ADOPT | unified LLM adapter, DeepSeek primary config, provider swap/fallback | WP07 | yes, Python optional dep |
| DeepSeek API | ADOPT PROVIDER | preference parsing, recommendation explanation, replan explanation, Copilot | WP07 after AI boundary tests | external optional |
| `pydantic/pydantic-ai` | ADOPT LATER | typed Copilot tool calling/evals, only if plain LiteLLM becomes insufficient | WP10+ | optional |
| `komoot/photon` | ADOPT PROVIDER | geocoding/autocomplete/reverse geocoding | post-WP06 discovery expansion | optional external/self-hosted |
| Overpass/OSM | ADOPT PROVIDER | real POI candidate enrichment | post-WP06 discovery expansion | optional external |
| `open-meteo/open-meteo` | ADOPT PROVIDER | weather context/risk input | WP06 after mock event path passes | optional external |
| `statelyai/xstate` | ADOPT | frontend workflow state only; backend remains authoritative | WP08 | yes, frontend |
| `shadcn-ui/ui` | ADOPT | UI components, not domain logic | WP08 | copied frontend components |
| `duo-labs/py_webauthn` | ADOPT | FastAPI-side WebAuthn/Passkey step-up trust layer | after WP04 commerce is stable, before production-like payment demo | optional Python dep |
| `microsoft/playwright` | ADOPT | Golden Scenario browser E2E and screenshot evidence | WP09 | dev dep |
| `stripe-samples/accept-a-payment` | REFERENCE + OPTIONAL ADAPTER | test payment implementation reference only; CityNexus PaymentProvider remains the boundary | WP10+ | no core dependency |
| `guberm/PlacesRecommendation` | REFERENCE PIPELINE | candidate -> enrichment -> validation -> scoring -> explanation -> cache | design borrowed; do not run .NET service by default | no |
| `wang-bool/Travel-Story` | REFERENCE UI/PROVIDERS | map/provider UX patterns only | frontend design reference | no |
| `TimefoldAI/timefold-solver` | OPTIONAL COMPARATIVE SOLVER | advanced Java/Kotlin solver experiment/benchmark | after OR-Tools path is stable | optional service only |

## Dependency discipline

Do not install `routingpy`, `ortools`, `litellm`, `webauthn`, MapLibre, Turf, XState and Playwright in one giant commit. Each dependency enters only with its own test gate and fallback path.
