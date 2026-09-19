# CityNexus V13.5 — Fully Grounded Journey Reality

Date: 2026-09-13 (Asia/Shanghai)  
Target: `CityNexus-V13.5-Fully-Grounded-Journey-Reality-20260913.zip`

## Outcome

V13.5 is implemented against the authoritative worktree. The sealed Tianjin
Golden now uses a Journey-shaped provider node set with distinct ARRIVAL and
DEPARTURE identities, Journey-specific Valhalla matrix evidence for WALK and
AUTO, deterministic candidate feasibility, authoritative Compose, PlanVersion
selection, and the existing JourneyTwin/UI path.

The selected Golden route facts contain zero `SYNTHETIC_FIXTURE` legs. Route
provenance and CityNexus cost-estimate provenance are separate fields in both
MobilityFact evidence and the serialized PlanVersion evidence.

## Delivered

- Actual structural Journey provider identities for anchors, activities, and
  protected commitment Places.
- Valhalla `sources_to_targets` parsing for both the compact duration/distance
  envelope and the route-cell envelope.
- Journey-scoped WALK and AUTO capture with sealed node identity, capture time,
  time basis, route provider, and explicit cost-estimate provenance.
- Fully grounded admission mode that blocks missing provider pairs instead of
  silently filling the Golden with synthetic legs; normal degraded mode remains
  mixed and explicitly labelled.
- DeepSeek Responses source extraction for nested web-search `action.sources`
  and message URL-citation annotations. Live web observations persist as
  non-authoritative until fact completion is tied to captured source IDs.
- V13.5 City Discovery UI state and a Playwright proof of the selected,
  fully-grounded Journey.

## Truth boundaries

No DeepSeek key was configured in the process environment for this run. The
live web-search canary was therefore not called; the parser was verified with
the sanitized nested Responses shape. No credential supplied in chat was
written to source, reports, databases, or the archive.

The sealed Open-Meteo payload retains explicit local-time semantics and reports
`WEATHER_WINDOW_UNCERTAIN` when its captured hourly window does not overlap the
requested future Journey window. No weather certainty is invented.

The final archive is validated by extracting it outside the repository and
executing the targeted backend runtime gate from that fresh extraction.
