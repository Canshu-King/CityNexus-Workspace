# GPT External Review Request

## Decision Requested

Review the supplied evidence and recommend a concrete implementation plan for
the P1 Association router. The plan must use a genus-0 Association port
allocation before geometry routing, then produce a full 18-Association
candidate through global routing with joint reroute support.

## Independently Reproduced Facts

| Case | V | E | F | Orientable genus | Result |
|---|---:|---:|---:|---:|---|
| Official candidate port ordering | 16 | 21 | 3 | 2 | FAIL |
| `PLAN_O_PRESERVE_LOCAL_GEOMETRY` | 16 | 21 | 7 | 0 | PASS |
| `PLAN_R_REVERSE_EMBEDDING` | 16 | 21 | 7 | 0 | PASS |

The topology reports are in `evidence/`. Both supplied port plans modify only
Association `sourcePortFraction`, `targetSide`, and `targetPortFraction`; they
do not override Extend routes or Association identity fields.

The current candidate is still geometrically invalid:

- `properCrossingCount = 0`, `collinearOverlapPairCount = 0`
- `contactPairCount = 46`, `uniqueContactCount = 55`
- `crossing = 0`, `overlap = 0`, `tjunction = 22`, `shared_endpoint = 33`
- `shortSegmentCount = 9`, `redundantCollinearPointCount = 88`
- V2 FAIL; V3 FAIL because its V2 dependency fails. V3 has no separate frozen
  Extend-contract failures.
- The recorded complete local suite is `51 passed`.

## Assessment of the Two Inputs

`inputs/topology-assist/` is the primary corrective input. It demonstrates a
necessary precondition that the earlier A* workbench lacks: under the current
rotation system, waypoint-only routing cannot reach a contact-free planar
embedding. `PLAN_O` is the preferred first seed because it retains more local
geometry; `PLAN_R` must remain available as an alternate seed.

`inputs/gpt-aid/` is a complementary implementation aid. Its bounded planner
correctly keeps the official candidate untouched, searches target sides, and
uses source fan-out reservations. Its own notes identify the `A-M-UC-08` /
`A-CE-09` oscillation and relevant mutable batches. The supplied implementation
does not yet implement the advice it describes: `_attempt()` still plans routes
sequentially, keeps accepted paths occupied, and changes only route order
between trials. It has no candidate-family selection, repeat-signature cycle
detection, or joint super-batch reroute.

## Required Planner Design

1. Apply a candidate port plan and reject it if the topology audit reports a
   non-zero genus or duplicate node-perimeter position.
2. Derive and retain a face/rotation scaffold from the selected planar plan.
3. For each mutable route, generate multiple deterministic homotopy families:
   default, top, bottom, inner/left, and outer/right. Target side and port
   fraction may vary only if the topology pre-gate remains zero-genus.
4. Search combinations by batch, not a permanent greedy sequence. Start with
   super-batch P (`A-M-UC-08`, `A-CE-09`, `A-PA-07`, `A-B-06`) and super-batch
   U10 (`A-CD-UC-10`, `A-M-UC-10`, `A-T-UC-10`, `A-T-UC-11`).
5. Record a repeat signature of failed route, blocker set, candidate family,
   and selected port plan. On a repeated signature, switch family or rip up
   the conflicting batch rather than repeating the same cost surface.
6. Preserve the Traveler and Provider horizontal fan-out bands supplied in the
   GPT aid during planning; normalize only after full geometry is found.
7. Compress paths to at most two decimal coordinates, remove collinear points,
   and reject segments below 0.10 cm before V2 and V3.

## Questions for Review

1. Does `PLAN_O` provide the best initial face scaffold, or does the supplied
   graph geometry make `PLAN_R` the more viable initial seed?
2. What exact per-route corridor/family constraints best preserve the selected
   rotation system while keeping fixed Extend geometry clear?
3. Should super-batches P and U10 be solved jointly or in an interleaved beam
   search, and which routes must be jointly mutable with them?
4. Is a 0.10 cm grid sufficient for a proof-quality search, or should the
   geometry layer use exact centimeter coordinates after coarse planning?

Do not treat either topology PASS or the 51 passing tests as completion. The
only promotion criterion remains a full official candidate with all defect
counts zero, V2 PASS, V3 PASS, and complete pytest PASS.
