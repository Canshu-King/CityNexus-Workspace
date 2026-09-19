# routingpy Reassessment

The Foundation already contains a routingpy adapter and it remains useful as a compatibility experiment. It should **not** become the mandatory CityNexus mobility foundation.

Reason:

- routingpy 1.3.0 is still useful conceptually and supports GraphHopper, OpenTripPlannerV2, Local Valhalla, OSRM, matrices and directions;
- however its latest PyPI release is from 2023 and the published testing metadata is centered on older CPython versions;
- CityNexus now targets Python 3.12 and Valhalla itself has current Python/Windows distribution support.

Therefore use this hierarchy:

```text
CityNexus MobilityProvider        authoritative abstraction
  |
  +-- ValhallaHTTPProvider        first real implementation
  +-- pyvalhalla adapter          optional local implementation
  +-- routingpy adapter           optional compatibility adapter
  +-- GraphHopper adapter         later
  +-- OpenTripPlanner adapter     transit, after usable GTFS exists
  +-- Mock/Frozen provider        always available fallback
```

This preserves the useful parts of routingpy without making CityNexus depend on its release cadence.
