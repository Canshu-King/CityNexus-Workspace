# P1 Route Contact Gate Result

Date: 2026-09-06

## Scope

The contact-gate patch was applied without modifying the protected domain model,
requirements, use-case specifications, semantic page YAML, or C1-C4 calibration.
No Visio document, RC6 artifact, or Part 2 page was generated.

## Result

`validate_p1_route_candidate_v2.py`: **FAIL**

- historical geometry gate: PASS
- semanticConnectorCount: 21
- candidateRouteCount: 21
- explicitGeometryRouteCount: 21
- properCrossingCount: 0
- collinearOverlapPairCount: 0
- contactPairCount: 46
- uniqueContactCount: 55
- T-junctions: 22
- shared endpoints: 33
- shortSegmentCount: 9
- redundantCollinearPointCount: 88

The route candidate therefore does not satisfy the zero-contact release gate.

## Static tests

`pytest visio-renderer/tests -q`: **47 passed, 1 failed**.

The failure is the pre-existing preparation-contract assertion that expects 18
routes to have `waypoints: null`; the current candidate intentionally contains
explicit geometry for all 21 routes. The patch's new contact-gate contract and
all other tests pass. The stale test was not modified because the requested edit
scope allowed only `phase1-routing-rc6-candidate.yaml`.

## Stop condition

No route status was promoted to `GEOMETRY_PASS_PENDING_EXTERNAL_FREEZE`; no
formal rendering was attempted. This package is for GPT external review of the
remaining route-planning failure.
