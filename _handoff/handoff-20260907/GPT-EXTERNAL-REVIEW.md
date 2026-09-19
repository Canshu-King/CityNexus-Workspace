# CityNexus P1 Route Repair V3 - External Review

Date: 2026-09-07
Reviewed package: `CityNexus-P1-Route-Repair-V3-GPT-Opinion-20260907(2).zip`

## Verdict

`REPAIR_REQUIRED` is confirmed. The V3 workbench/gate design is directionally correct, but the current route candidate is not eligible for RC6 promotion, Visio rendering, or final freeze.

The current failure is geometric contact quality, not semantic connector completeness:

- semanticConnectorCount = 21
- candidateRouteCount = 21
- explicitGeometryRouteCount = 21
- properCrossingCount = 0
- collinearOverlapPairCount = 0
- Contact Gate = FAIL
- contactPairCount = 46
- uniqueContactCount = 55
- T-junction = 22
- shared_endpoint = 33
- shortSegmentCount = 9
- redundantCollinearPointCount = 88

## Reproduction note

The isolated review package contains only the supplied subset of tests. Running those tests locally from this package produced:

`8 passed`

The package documentation states that the complete workspace produced `51 passed / 0 failed`. That full-workspace result cannot be independently reproduced from this review package alone, so treat `51/51` as a workspace claim rather than an artifact-contained reproduction. This is not evidence that the claim is false.

`validate_p1_route_candidate_v3.py` was also executed. The historical/base route validator passes its existing crossing/overlap checks, while the hardened Contact Gate fails with the counts above. V3 therefore correctly remains FAIL through the V2 dependency. This is the intended gate behavior and should not be weakened.

## Important correction to the current repair narrative

`P1_UC_ROUTE_REPAIR-WORKLIST.json` reports `associationRepairCount = 16`, not 18. The two Association routes currently showing zero contacts are:

- `A-CD-UC-04`
- `A-CD-UC-05`

Therefore, do not describe all 18 Association routes as individually proven defective. A global rip-up may still move either of these two if a new corridor plan requires it, but they should be treated as preserve-if-possible anchors rather than mandatory first-line repairs.

## Feasibility finding

There is no evidence of an inherent topological deadlock caused solely by the three frozen Extend routes.

As an independent geometry experiment, a nine-route Traveler Association skeleton was constructed while keeping all three Extend routes byte-for-byte geometrically frozen. The supplied routing geometry/contact functions reported:

- node/interior/orthogonality/segment/redundancy failures = 0
- inter-route contacts = 0

This does **not** prove that all 18 Association routes can be completed without further changes. It does prove that the Traveler subgraph can be laid out cleanly around the frozen Extend obstacles, so the repair should proceed as a global corridor/port-allocation problem rather than as a reason to relax the Contact Gate or alter Extend geometry.

The validated sub-solution is included as `traveler-corridor-skeleton.yaml`. It is evidence and a starting corridor skeleton, not a merge-ready final candidate.

## Geometry observations that should influence the next plan

1. `EXT-07-06` forms a vertical barrier at approximately `x = 8.3` between `y = 6.6` and `y = 9.7`. `A-T-UC-06 -> UC-06 RIGHT` is a sound preference. Clean LEFT access is unnecessarily constrained.

2. `EXT-09-08` forms a hook around UC-08. The current hint that both Traveler/Mobility should naturally approach `UC-08 RIGHT` must not become a hard constraint. The independently validated Traveler skeleton reaches `UC-08 BOTTOM` on the right half (`x = 12.5`) cleanly while the frozen Extend retains the bottom-center port (`x = 11.1`). This leaves a distinct approach family available for Mobility.

3. `EXT-10-09` creates a right-side wall at `x = 27.0`, plus a lower horizontal section at `y = 14.2`, and contributes to a central barrier near UC-09/UC-10. A Traveler route to UC-10 should cross the central region above the `EXT-09-08` horizontal at `y = 10.2`; the validated skeleton uses a corridor at about `y = 10.1` and enters `UC-10 LEFT`.

4. For UC-10, the frozen Extend keeps the TOP-center port. `A-CD-UC-10` and `A-M-UC-10` can still plausibly use distinct TOP ports on the left half, while `A-T-UC-10` uses LEFT. The three routes must be planned together, not greedily one at a time.

5. `A-B-06` and `A-PA-07` should use separated lanes above the top segment of `EXT-10-09` (`y < 9.4`), but the source-side provider routes above them must not be allowed to form a new barrier that seals this corridor.

6. `A-CE-09 -> UC-09 LEFT` remains a reasonable lower-corridor preference.

7. `A-T-UC-11` is a sensitive central route. It must be co-planned with the UC-10 provider routes. Freezing it early after a local clean result can block the later central passage.

## Review of the worklist strategy

The priority score is useful for diagnosis, but `repairOrder` must **not** be interpreted as a safe sequential freeze order. The score reflects contacts in the current bad geometry. Orthogonal routing is globally coupled: changing one high-priority route changes the available corridors and the conflict graph for several later routes.

Use the worklist as a list of routes needing attention, then perform port allocation and corridor reservation globally. If a batch fails, rip up the batch and change port/corridor assignments. Do not solve each contact with 0.02-0.05 cm micro-jogs.

## Gate policy

Keep the hardened Contact Gate and V2/V3 contracts unchanged.

Do not set final metadata or Association planning status until all required geometry gates are clean. Only after V2 is fully PASS with zero contact/short/redundant counts should the candidate be promoted to:

- metadata status: `GEOMETRY_PASS_PENDING_EXTERNAL_FREEZE`
- Association planningStatus: `ROUTE_PLANNED_PENDING_EXTERNAL_FREEZE`

Until then:

- do not render Visio;
- do not generate/promote RC6;
- do not start Part 2 on the assumption that P1 routing is frozen.
