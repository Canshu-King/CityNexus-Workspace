# Codex Next Instructions - CityNexus P1 Route Repair V3

Work from the current repository/workspace, not from this review ZIP as a replacement repository.

## Objective

Produce a globally coherent zero-contact orthogonal routing plan for the 18 Association routes while preserving the three frozen Extend routes exactly.

Do not weaken validators to make the candidate pass. Fix the geometry.

## Non-negotiable constraints

- Preserve these three Extend routes exactly, including fields, sides, fractions, waypoints, and planning status:
  - `EXT-07-06`
  - `EXT-09-08`
  - `EXT-10-09`
- Preserve semantic source/target connector meaning from `visio-spec/pages/p1_uc_overview.yaml`.
- Keep all waypoint coordinates to at most 2 decimal places in the final candidate.
- Do not introduce segments shorter than `0.10 cm`.
- Remove redundant collinear waypoints.
- Do not share unrelated intermediate waypoints or corridor nodes.
- Do not render Visio or promote RC6 before V3 PASS.
- Do not change gate thresholds or contact classification to hide defects.

## Correct the planning model before editing more waypoints

Add an explicit port-allocation/corridor pre-plan for all Association routes. It may be a temporary YAML/JSON/table or a small planning script, but it must make these decisions visible before the final candidate is rewritten:

- route ID
- source side and source port slot/fraction
- target side and target port slot/fraction
- reserved horizontal/vertical corridor family
- batch/dependency group

Treat `P1_UC_ROUTE_REPAIR-WORKLIST.json` as diagnostic priority only. Do not reroute one route, freeze it, then blindly continue down `repairOrder`.

## Preserve-if-possible anchors

The current audit reports zero contacts for:

- `A-CD-UC-04`
- `A-CD-UC-05`

Do not call these two defective. Preserve them if they remain compatible with the new global corridor plan. Move them only when a documented global-passage reason requires it.

## Recommended batch plan

### Batch A - Traveler corridor skeleton

Use `traveler-corridor-skeleton.yaml` as a validated sub-solution/corridor reference, not as a blind final merge.

It has already been checked together with all three frozen Extend routes and produced zero geometry failures and zero route contacts within that subgraph.

Important properties to preserve unless a later global conflict proves otherwise:

- top fan ordering from Traveler uses distinct source/lane positions;
- `A-T-UC-06` enters `UC-06 RIGHT`;
- `A-T-UC-10` uses the corridor around `y = 10.1` and enters `UC-10 LEFT`;
- `A-T-UC-08` may use `UC-08 BOTTOM` on the right half rather than RIGHT;
- `A-T-UC-12` uses a lower-left approach without touching `EXT-09-08`.

Do not mark Batch A final merely because it is clean in isolation. Keep it eligible for rip-up if later provider routes prove a global conflict.

### Batch B - UC-10 central/provider group

Co-plan these routes and the central Traveler routes:

- `A-CD-UC-10`
- `A-M-UC-10`
- `A-T-UC-10`
- `A-T-UC-11`

Initial policy:

- frozen `EXT-10-09` keeps `UC-10 TOP` center;
- assign `A-CD-UC-10` and `A-M-UC-10` distinct TOP ports on the left half;
- keep `A-T-UC-10` on LEFT if feasible;
- reserve a central passage so `A-T-UC-11` does not become a barrier for provider routes.

If this batch deadlocks, change Association port sides/slots before considering any changes to frozen Extend geometry.

### Batch C - Booking / Payment Authorizer upper-right group

Co-plan:

- `A-B-06`
- `A-PA-07`

Use separated channels with `y < 9.4` while crossing the right-side region. Ensure other provider routes do not close those channels before these two are placed.

### Batch D - Mobility / Context lower group

Co-plan:

- `A-M-UC-08`
- `A-CE-09`
- any remaining Mobility routes that constrain the same corridor

Do not hard-code the old `A-M-UC-08 -> UC-08 RIGHT` hint if it conflicts with the global plan. The frozen Extend already uses UC-08 bottom-center and the validated Traveler skeleton demonstrates that a separate bottom-right slot is usable. Allocate distinct ports/corridors globally.

`A-CE-09 -> UC-09 LEFT` is a preferred starting point, not an immutable semantic requirement.

### Batch E - Anchor compatibility and cleanup

Re-evaluate `A-CD-UC-04` and `A-CD-UC-05` against the completed route set. Keep them unchanged if clean. If they must move, record the corridor conflict that required the move.

Then simplify all routes:

- delete redundant collinear points;
- eliminate short segments;
- normalize coordinates to <= 2 decimal places;
- verify no intermediate waypoint is shared by unrelated routes.

## Validation loop

After each coherent batch, run the relevant base/contact checks. At minimum, before accepting the completed geometry run:

```text
python calibration/validate_p1_route_candidate.py
python calibration/audit_p1_route_contacts.py
python calibration/validate_p1_route_candidate_v2.py
python calibration/validate_p1_route_candidate_v3.py
```

Also run the full repository test suite from the actual workspace. The external review package itself only contains enough tests to reproduce `8 passed`; the package's documented `51 passed / 0 failed` refers to the full workspace and should be re-established there.

## Final acceptance conditions

Do not update final statuses until all of these are true at once:

- base route validation PASS;
- Contact Gate PASS;
- `contactPairCount = 0`;
- `uniqueContactCount = 0`;
- `crossing = 0`;
- `overlap = 0`;
- `tjunction = 0`;
- `shared_endpoint = 0`;
- `shortSegmentCount = 0`;
- `redundantCollinearPointCount = 0`;
- V2 PASS;
- all 3 frozen Extend routes remain exact;
- full repository tests PASS.

Only then set:

- metadata `status: GEOMETRY_PASS_PENDING_EXTERNAL_FREEZE`
- every Association `planningStatus: ROUTE_PLANNED_PENDING_EXTERNAL_FREEZE`

Then run V3 one final time. V3 must PASS before any Visio rendering or RC6 promotion.

## Failure handling

If a batch cannot be completed cleanly, do not add micro-jogs and do not relax the audit. Report the smallest blocking route set, the occupied corridor/port slots, and propose a port-side reassignment for one or more Association routes. Prefer rip-up-and-reroute of the affected batch over accumulating local exceptions.
