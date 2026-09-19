# Solver Runtime V1 Architecture

```text
existing deterministic replacement choices
+ current execution location and disruption time
+ Journey horizon and remaining budget
+ verified candidate opening windows
+ next durable C4 semantic/time anchor
+ one operation-scoped frozen MobilitySnapshot
        |
        v
pure immutable ReplanSolverProblem
        |
        v
optional OR-Tools CP-SAT (one worker, fixed seed, bounded time)
        |
        v
distinct SolverCandidate assignments
        |
        v
existing PlanVersion/Activity materializer
        |
        v
existing CityNexus deterministic feasibility gate
using the exact same MobilitySnapshot
        |
        v
verified scoring + ReplanDiff + PRESENTED proposal
```

V1 mutates only the disrupted flexible slot. Completed prefix Activities and all other Activities are copied unchanged. The next C4 Activity is a fixed protected anchor and is checked again after materialization.

`F4_ORTOOLS_WINDOW_REPLACEMENT` carries an explicit candidate start time. Solver schedule data is not stored as F3 opportunity-window evidence. Drop uses the existing optional-removal semantics only for an unlocked non-C4 affected Activity.

Proposal evidence records generator kind, solver and terminal status, stable problem and assignment fingerprints, exact MobilitySnapshot ID, deterministic rank, and `feasibility_authority=CITYNEXUS_DETERMINISTIC_GATE`.

Solver core modules import no FastAPI, SQLAlchemy, HTTP, provider, database, or integration modules. Missing frozen mobility pairs make an assignment unavailable and are never interpreted as zero travel.
