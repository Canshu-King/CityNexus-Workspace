# Provider Truth Evidence

## Sealed candidate capture

`data/replay/tianjin_real_snapshot.json` is the captured provider bundle. It contains five Nominatim candidates, a captured Valhalla matrix, Open-Meteo hourly data, and an explicit `evidence_completion` section. Captured mode never falls back to the handcrafted `_TIANJIN_REPLAY` list.

The completed candidate is the OSM object `way/73422999`, materialized as a Journey-owned `real-place-*` record. Its official identity reconciliation is recorded as `天津文化中心` → `天津博物馆`; the coordinate and provider identity remain from the provider capture.

## Official source completion

The sealed completion records:

- `https://www.tjbwg.cn/cn/Notice.aspx` (`OFFICIAL_WEB`) — Tuesday–Sunday 09:00–16:30, last admission 16:00, Monday closed.
- `https://www.tjbwg.cn/cn/Ticketing.aspx` (`OFFICIAL_TICKETING`) — free public admission under the official ticketing policy, subject to separately charged exhibitions.

Only facts whose `source_observation_ids` resolve to captured `WebObservation` rows are promoted. Candidates without captured official evidence retain `UNKNOWN` hours/cost and are rejected by `DETERMINISTIC_PROVIDER_FACT_GATE`.

## Mobility

The selected PlanVersion contains an actual `valhalla` / `CAPTURED_REPLAY` AUTO fact for the selected materialized Place. The complete plan also retains synthetic fixture facts for uncovered structural or protected-commitment pairs. The evidence records both components and explicitly declines the stronger “fully real matrix” claim.

The implementation also records the Journey-derived capture anchor in discovery/provider status and uses the Journey-aware anchor for candidate distance and semantic context. The frozen mobility bundle’s original captured anchor remains visible as sealed source evidence; it is not rewritten as if a new live route matrix had been captured.

## Weather

Weather evidence is sliced by the semantic intent window. If the sealed snapshot has no matching hour, the response contains `SEALED_REPLAY_OUT_OF_REQUEST_WINDOW` and `WEATHER_WINDOW_UNCERTAIN`. This is intentional evidence honesty.
