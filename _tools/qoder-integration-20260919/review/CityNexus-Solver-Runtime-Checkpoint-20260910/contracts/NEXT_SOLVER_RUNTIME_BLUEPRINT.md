# Next Stage Blueprint - Real OR-Tools Candidate Generation

Start only after Weather Runtime Hardening is externally frozen.

## Product purpose

OR-Tools should improve candidate generation for the mutable part of a Journey. It must never become CityNexus's feasibility authority.

Correct chain:

```text
Frozen Journey facts
+ completed execution prefix
+ protected C4 anchors
+ mutable suffix
+ opening windows
+ budget
+ frozen MobilitySnapshot
+ deterministic candidate-place facts
        -> OR-Tools candidate generator
        -> SolverCandidate(s)
        -> materialize candidate PlanVersion
        -> existing authoritative validate_plan_feasibility(snapshot)
        -> verified scoring
        -> ReplanDiff
        -> ReplanProposal
        -> user acceptance + acceptance-time revalidation
```

## Recommended first increment

Do not begin with a general travelling-salesman optimizer. The current Golden Scenario does not need an academic fireworks display.

Model a constrained mutable-suffix/replacement problem first:

- completed prefix is outside the solver and immutable;
- current execution position is fixed input;
- durable C4 Activities are mandatory and fixed at stable semantic key + start time;
- disrupted mutable Activity can be replaced by one of deterministic alternative Places or dropped when allowed;
- other mutable suffix Activities remain required initially;
- start times may move only inside explicit windows;
- all travel comes from one frozen MobilitySnapshot;
- budget and Journey end are hard constraints;
- opening hours are hard constraints;
- C4 presence/start are hard constraints.

This is already a real CP-SAT scheduling problem and can later expand to optional insertion and ordering.

## Suggested pure domain types

```python
@dataclass(frozen=True)
class SolverActivityOption:
    option_key: str
    semantic_key: str
    duration_min: int
    cost_minor: int
    earliest_start_min: int
    latest_end_min: int
    required: bool
    protected: bool
    original_start_min: int | None

@dataclass(frozen=True)
class SolverAnchor:
    semantic_key: str
    start_min: int
    duration_min: int

@dataclass(frozen=True)
class ReplanSolverProblem:
    journey_id: str
    operation_key: str
    journey_start_min: int
    journey_end_min: int
    budget_max_minor: int
    current_location_key: str
    completed_prefix_keys: tuple[str, ...]
    protected_anchors: tuple[SolverAnchor, ...]
    replacement_options: tuple[SolverActivityOption, ...]
    frozen_mobility_snapshot_id: str
```

Do not put SQLAlchemy objects, HTTP clients, or FastAPI Request objects in the solver model.

## CP-SAT variables for v1

For each replacement option `i`:

- `present_i : BoolVar`
- `start_i : IntVar`
- `end_i = start_i + duration_i`

For protected anchors:

- fixed presence = 1
- fixed start = durable C4 scheduled start

Replacement group:

- exactly one valid replacement, or
- at most one + explicit drop option if dropping is allowed.

## Constraints

1. Journey window.
2. Opening hours.
3. Budget.
4. Completed prefix cannot be changed.
5. Protected C4 cannot be removed/moved.
6. No overlap.
7. Frozen travel between selected stages.
8. Arrival before next protected anchor with safety/travel requirement where relevant.
9. No use of live provider calls.

## Objective

Keep solver objective deliberately secondary to the authoritative gate.

A reasonable deterministic first objective is lexicographic in spirit:

1. preserve mandatory/protected facts (already hard constraints),
2. minimize dropped optional Activity count,
3. minimize total schedule shift,
4. minimize travel minutes,
5. prefer deterministic precomputed preference value,
6. stable option-key tie break outside or encoded safely.

Do not reimplement the final CityNexus Contextual Journey Utility Score inside CP-SAT. The existing verified scoring layer remains the product ranking authority after feasibility.

## Top-K

Need multiple proposals, not one magical optimum.

Recommended approach:

1. solve deterministic best candidate;
2. materialize assignment fingerprint;
3. add a no-good constraint excluding the exact assignment;
4. solve again;
5. repeat until K, infeasible, or deterministic time limit.

Every candidate still passes the CityNexus Gate independently.

## Determinism

- `num_search_workers = 1`
- fixed `random_seed`
- explicit max solver time
- stable input sorting
- stable materialization ordering
- stable post-gate ranking

## Failure/fallback

If OR-Tools:

- is not installed,
- returns UNKNOWN due timeout,
- raises controlled solver error,
- produces zero post-gate candidates,

then CityNexus should retain the existing deterministic heuristic candidate path.

Never promote a partial/unverified solver assignment merely because a timeout occurred.

## Provenance

Replan evidence should distinguish:

```json
{
  "generator": {
    "kind": "ORTOOLS_CP_SAT",
    "version": "...",
    "problem_fingerprint": "...",
    "solver_status": "OPTIMAL|FEASIBLE",
    "rank": 0
  },
  "feasibility_authority": "CITYNEXUS_DETERMINISTIC_GATE"
}
```

Do not label OR-Tools itself as `verified feasibility`.

## Acceptance tests

- ORT-01 completed prefix cannot move
- ORT-02 C4 semantic key and start cannot move/disappear
- ORT-03 solver uses supplied frozen mobility and performs no live network
- ORT-04 malicious/invalid solver candidate is rejected by CityNexus Gate
- ORT-05 fixed workers/seed produces reproducible assignment
- ORT-06 opening hours respected
- ORT-07 optional Activity may be dropped instead of C4
- ORT-08 budget hard constraint respected by solver and rechecked by Gate
- ORT-09 OR-Tools missing -> deterministic fallback still works
- ORT-10 offline Golden Scenario still works
- ORT-11 solver provenance visible and feasibility authority remains CityNexus
- ORT-12 same frozen input produces stable post-gate ordering
- ORT-13 top-K candidates are unique
- ORT-14 timeout/UNKNOWN cannot yield an unverified proposal
- ORT-15 solver input contains no SQLAlchemy/HTTP mutable runtime object
- ORT-16 acceptance-time feasibility revalidation remains unchanged

## Hard stop

When ORT tests and all prior Golden/Provider/Weather gates pass, checkpoint for external review before adding LiteLLM/DeepSeek.
