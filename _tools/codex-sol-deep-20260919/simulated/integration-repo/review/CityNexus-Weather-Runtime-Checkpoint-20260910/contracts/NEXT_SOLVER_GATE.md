# Next Gate Preview - OR-Tools Runtime Candidate Generation

Start only after Weather Runtime is externally accepted as `FROZEN_PASS`.

## Existing foundation

Current repo already contains:

- `ORToolsVariantSelector`
- `ReplanCandidateEvidence`
- `generate_ortools_candidates()` placeholder/ranking boundary
- deterministic verified candidate ranking
- authoritative feasibility
- frozen MobilitySnapshot runtime
- C4 protection

The current OR-Tools adapter is only a small selector over already-generated variants. It is not yet a real Journey candidate generator.

## Intended authority chain

```text
frozen Journey facts
+ frozen MobilitySnapshot
+ Activity time windows
+ mutable suffix
+ protected C4 anchors
-> OR-Tools generates candidate schedule(s)
-> persist candidate PlanVersion
-> authoritative CityNexus feasibility gate
-> verified scoring
-> ReplanProposal
```

OR-Tools is a generator, never the authority.

## Suggested future tests

- ORT-01 completed prefix cannot move
- ORT-02 C4 start/location cannot move or disappear
- ORT-03 candidate uses frozen mobility, no live network
- ORT-04 solver candidate still rejected if CityNexus Gate fails
- ORT-05 deterministic seed/workers -> reproducible candidates
- ORT-06 time windows/opening hours respected
- ORT-07 optional activity may be dropped instead of C4
- ORT-08 budget hard constraint remains authoritative
- ORT-09 no OR-Tools installed -> deterministic fallback still works
- ORT-10 offline Golden Scenario remains operational
- ORT-11 solver provenance is visible but not mislabeled as feasibility authority
- ORT-12 same input facts produce stable candidate ordering

Do not implement this gate during Weather Runtime work. This file exists only to keep the road ahead obvious.
