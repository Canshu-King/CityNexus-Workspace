# V13.3 Golden Real-City Evidence

## Reproduced path

The repository test `backend/tests/test_v13_3_real_city_intelligence.py::test_v133_golden_real_city_intelligence_replay_preserves_cruise` proves:

1. ARRIVAL, MID_TRIP cruise, and DEPARTURE artifacts are confirmed into the Journey.
2. DeepSeek chooses the symbolic `UPCOMING_COMMITMENT` anchor; coordinates remain server-owned.
3. An intentionally fabricated candidate ID is rejected before planning.
4. Replay discovery returns bounded Tianjin candidates with normalized opening hours and explicit cost evidence.
5. The deterministic provider-fact gate controls eligibility.
6. A real materialized Place reaches authoritative Compose.
7. The paid `place-river-cruise` commitment remains in the composed PlanVersion.
8. Frozen discovery and weather provenance are present in PlanVersion mobility evidence.
9. The PlanVersion is selected and therefore becomes the JourneyTwin/UI/map source of truth.

## Browser evidence

The Playwright CLI flow at `/v8/discover` submitted traveler intent, displayed `SEALED_REPLAY_SEMANTIC_FALLBACK`, `DETERMINISTIC_PROVIDER_FACT_GATE`, and `SELECTED`, then opened `/v8/authoritative`. The authoritative surface displayed the materialized Tianjin Gallery and Haihe Riverside Design Library activities with frozen evidence.

## Provenance labels

- Semantic fallback: `SEALED_REPLAY_SEMANTIC_FALLBACK`
- Discovery replay: `SEALED_PROVIDER_REPLAY`
- Weather: replayed Open-Meteo snapshot with provider and capture timestamp
- Route/mobility: existing frozen CityNexus provider evidence attached to Compose
- Authority: deterministic feasibility plus existing PlanVersion selection gate

