# OR-Tools Runtime Gap Analysis Based on Current Repo

The repo contains useful scaffolding, but OR-Tools is not yet a real Journey candidate generator.

## What exists

- `app/planning/ortools_adapter.py::ORToolsVariantSelector`
  - CP-SAT chooses one item from variants that were already generated.
  - It does not model Activities, time windows, travel, C4, budget, or a mutable suffix.

- `app/planning/replan_candidate_problem.py`
  - `ReplanCandidateEvidence`
  - deterministic ranking and take-feasible helpers
  - `generate_ortools_candidates()` currently delegates to deterministic filtering/ranking.

- authoritative `validate_plan_feasibility()`
- frozen MobilitySnapshot runtime
- durable C4 hard-constraint translation
- existing heuristic Replan families F0/F1/F2/F3
- verified scoring and ReplanDiff

## What is missing

1. No solver problem object containing frozen Journey facts.
2. No CP-SAT Activity start/presence variables.
3. No solver representation of completed prefix vs mutable suffix.
4. No fixed C4 anchor constraints in CP-SAT.
5. No opening-hours/time-window constraints in solver.
6. No frozen MobilitySnapshot travel constraints in solver.
7. No hard budget constraint in solver.
8. No top-K unique schedule generation.
9. No materialization boundary from SolverCandidate to PlanVersion.
10. No explicit solver provenance in Replan evidence.
11. No runtime fallback contract for missing/timed-out OR-Tools.
12. OR-Tools is not declared as an optional project dependency in the current pyproject.

## Recommendation

Do not replace the existing heuristic Replan engine in one jump.

Introduce OR-Tools behind a candidate-generator boundary. Keep all current authoritative feasibility, C4, verified scoring, persistence, acceptance revalidation, and offline fallback unchanged.
