# CityNexus V13.3 Final Report

## Outcome

V13.3 adds a real-city intelligence vertical slice to the preserved V13.2 baseline:

`Journey Memory + intent -> DeepSeek DiscoveryIntent -> server anchor -> bounded provider/replay discovery -> materialized Place -> deterministic gate -> authoritative Compose -> selected PlanVersion -> JourneyTwin/UI/map`

The sealed replay flagship is proven. The live DeepSeek provider probe was attempted with a process-only key and returned provider errors for all four text cases; it is therefore reported as `NOT_PROVEN`, not as a live PASS.

## Implementation delivered

- DeepSeek V4 text and dedicated vision model configuration.
- Responses API JSON Schema output for reservation interpretation, DiscoveryIntent, and candidate curation.
- Explicit `candidate_journey_match` normalization and high-confidence mismatch confirmation gating.
- Semantic context limited to the active PlanVersion’s activities.
- Journey-derived discovery anchors ordered from current activity, hotel, Journey Memory arrival, protected commitment, and departure.
- Bounded Nominatim/Overpass discovery with sealed Tianjin replay.
- Stable real Place materialization with opening-hour normalization, cost evidence, provenance, capture and expiry fields.
- DeepSeek curation restricted to server-provided candidate IDs; deterministic provider-fact gating remains authoritative.
- Frozen discovery, route, mobility, and weather evidence persisted into the composed PlanVersion.
- New `POST /api/v1/journeys/{journey_id}/real-city/intelligence` path.
- City Discovery UI route with provenance, semantic rationale, feasibility, candidates, and authoritative-plan handoff.
- Existing authoritative execution, JourneyTwin, offline, and map surfaces consume the selected PlanVersion.

## Validation status

| Gate | Result | Runtime label |
|---|---|---|
| V13.3 focused backend | PASS | `SEALED_PROVIDER_REPLAY` / deterministic fake DeepSeek |
| Supplied prep checks | PASS | mocked Responses contract and semantic mismatch |
| Frontend production build | PASS | local Vite build |
| Browser City Discovery -> authoritative plan | PASS | sealed replay, local runtime |
| Broad backend regression | PASS: 385 passed, 2 skipped | local test runtime |
| Live DeepSeek text canary | NOT_PROVEN: 4 provider errors | live provider attempt |
| Live vision canary | SKIPPED | no reservation image supplied |
| Fresh-extract release gate | PASS: 12 backend tests; fresh frontend install/build | extracted source, isolated SQLite runtime |

## Runtime honesty

This was a bounded implementation/convergence run, not a nine-hour autonomous budget. Exact start time was not captured. No API key, database, cache, virtual environment, or frontend build output is intended for the release archive.
