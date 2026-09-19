# V13.5 Full Provider Grounding Evidence

## Sealed snapshot

- File: `data/replay/tianjin_v135_journey_snapshot.json`
- Schema: `citynexus.real-city.snapshot.v135`
- Captured at: `2026-09-13T13:43:17.079369+00:00`
- Mobility provider: Valhalla
- Structural nodes: 8
- Matrix facts: 128 cells, including diagonal closure cells; 56 directed
  non-diagonal legs per mode
- Modes: WALK (`pedestrian`) and AUTO (`auto`)

The node set includes `anchor:arrival`, `anchor:departure`,
`commitment:place-river-cruise`, and captured Place identities for the sealed
Tianjin candidate set. The composition layer matches Place/external identity,
role, and coordinates before accepting a provider fact.

## Selected-plan evidence

The Golden request uses `require_fully_grounded=true`. The deterministic gate
then consumes only the frozen Journey matrix and fails the operation if any
structural pair lacks a provider fact. The selected PlanVersion observed:

```text
runtime_label: FULLY_GROUNDED_JOURNEY
selected_route_provider_grounded: true
edit_matrix_provider_grounded: true
selected_synthetic_fact_count: 0
route_provenances: CAPTURED_REPLAY
cost_provenances: CITYNEXUS_COST_ESTIMATE
```

Valhalla supplies time and distance. CityNexus keeps the bounded AUTO fare
estimate and free WALK rule in a separate cost provenance field; route facts
are never presented as fare evidence.

## Weather boundary

The snapshot carries Open-Meteo hourly data with `Asia/Shanghai` local-time
semantics. The orchestration response exposes capture time, requested window,
coordinates, and coverage status. The current Golden date is outside the
sealed hourly window, so the result is explicitly uncertain rather than
silently treated as a current forecast.
