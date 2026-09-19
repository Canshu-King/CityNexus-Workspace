# V13 Provider Truth Record

This is the runtime provenance record for the final review package. Values are
status booleans and labels only; no secret value is written here.

## Current process

| Capability | Observed state |
| --- | --- |
| DeepSeek/API key | Not configured (`ai_key=false`) |
| Hermes URL/key | Not configured (`hermes_url=false`, `hermes_key=false`) |
| Guardian signal provider | `demo` |
| Real-city mode | `replay` |
| Phoenix external endpoint | Not configured in the current process |
| Local MCP | Available and tested (`6 passed`) |
| Local adversarial evaluation | Deterministic adapter `13/13`; not a model-backed Promptfoo CLI run |

## Sealed Tianjin replay

`data/replay/tianjin_real_snapshot.json` records a captured Tianjin snapshot:

- captured at `2026-09-12T03:15:03.659327+00:00`;
- Nominatim anchor and candidate discovery: `CAPTURED`;
- Overpass: `NO_RESULTS` (not silently treated as success);
- Valhalla mobility: `CAPTURED`, 36 frozen facts;
- Open-Meteo weather: `CAPTURED`, 24 hourly facts;
- candidate count: 5.

The replay normalizer preserves provider, capture time, fallback/degradation
and route geometry fields. The deterministic gate can consume this sealed
evidence without making a network call.

## V13 composer distinction

The V13 authoritative composer Golden uses `SYNTHETIC_FIXTURE` mobility rows so
the flagship remains repeatable without internet access. Its evidence states
`provider_evidence.selected_path=SYNTHETIC_FIXTURE` and explicitly says it is
not live production provider evidence. A mixed matrix is classified as
`MIXED_PROVIDER_FACTS`; it cannot be promoted to a full captured-provider
claim. Captured replay and live capture are accepted paths when supplied by the
provider boundary.
