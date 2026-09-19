# Real-City Truth V2 Evidence

## Fresh capture

The developer command `python scripts/capture_tianjin_real_city_snapshot.py` was rerun during this iteration. The sealed fixture records capture time `2026-09-12T03:15:03.659327+00:00` (UTC) and the following provider states:

| Provider | State | Interpretation |
| --- | --- | --- |
| Nominatim anchor | `CAPTURED` | Name/address/anchor grounding. |
| Overpass | `NO_RESULTS` | Category discovery was attempted; no Overpass result was relabeled as a success. |
| Nominatim candidate fallback | `CAPTURED` | Five real OSM candidate records were retained after the bounded Overpass attempt. |
| Valhalla | `CAPTURED` | Six route nodes and 36 directed travel facts were frozen into the replay fixture. |
| Open-Meteo | `CAPTURED` | Hourly weather facts were sealed for deterministic replay. |

Candidate records contain provider identity, OSM identifiers, coordinates, normalized opening status, and cost evidence. The current capture legitimately contains `UNKNOWN` opening hours and `UNKNOWN` cost for candidates where OSM did not provide those facts. The application does not convert those values into all-day availability or zero cost.

## Application path

- The live discovery path derives its search anchor from Journey places/routes/current location.
- Nominatim is used for grounding; Overpass is the bounded category-discovery source.
- `LIVE` and `CAPTURED_REPLAY` use the same discovery/materialization contract.
- Autonomous candidate evaluation requires normalized, non-unknown availability and explicit/estimated cost evidence where the policy requires it.
- Frozen mobility evidence is attached before deterministic CP-SAT evaluation.

## Reproducibility

The V7 flagship test exercised `mode=captured_replay` and asserted `SEALED_LIVE_CAPTURE`, candidate opening-hours fields, and candidate cost-evidence fields. Full backend regression and Playwright regression were rerun after the V7 changes.
