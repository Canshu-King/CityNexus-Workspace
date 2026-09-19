# OR-Tools Advanced Candidate Generator

Do not let OR-Tools replace the CityNexus feasibility gate.

Target boundary:

```text
verified Journey/Constraint/Commitment facts
+ frozen MobilitySnapshot
→ OR-Tools candidate generator
→ candidate PlanVersion(s)
→ authoritative feasibility gate
→ verified scoring
→ ReplanProposal
```

The prepared module `replan_candidate_problem.py` provides a deterministic evidence/ranking boundary that both heuristic and OR-Tools candidates can share.

## First useful OR-Tools problem

Model only the mutable suffix:

- completed/terminal prefix fixed;
- current execution position fixed;
- C4 anchors pinned;
- optional flexible Activities selectable;
- candidate Places have duration, cost, time windows;
- travel times come from frozen facts;
- budget is hard;
- journey end is hard;
- opening windows are hard;
- minimize disruption / travel and maximize verified utility.

Do not begin with a city-scale universal TSP. We are trying to finish a course project, not found an optimization laboratory.

## Output requirements

Every OR-Tools candidate must carry:
- candidate family/source = `ORTOOLS`;
- evidence inputs used;
- no mutable live-provider handles;
- deterministic seed/worker settings where applicable;
- full post-solve gate result.

If OR-Tools is unavailable, heuristic F0/F1/F2/F3 remains fully functional.
