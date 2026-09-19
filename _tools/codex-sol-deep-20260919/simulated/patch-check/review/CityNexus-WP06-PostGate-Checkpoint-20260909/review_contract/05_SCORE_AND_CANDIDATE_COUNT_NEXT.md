# Replan Scoring and candidate_count — Next Required Design

## Current drift

Replan generation changes Activities but currently copies:

```text
utility_score
score_breakdown_json
```

from the base PlanVersion.

This makes a new plan look quantitatively identical even when cost, schedule, travel, or disruption exposure changed.

Also, `ReplanGenerateRequest.candidate_count` accepts 1..5 but the current implementation creates one proposal.

## Do not fake scoring

Do not merely perturb the old score by a constant.

Before exposing replan comparison to the frontend/AI, derive score metrics from verified proposed-plan facts. Preserve the established Contextual Journey Utility Score weights where they are actually computable.

Recommended deterministic evidence sources:

```text
commitment preservation <- durable C4 validation
stability               <- ReplanDiff changed/moved/removed/added
budget fit               <- proposed total vs Journey budget
mobility fit             <- frozen mobility travel facts / travel delta
time reliability         <- FeasibilityEnvelope slack/buffer
robustness               <- constraint slack + degraded provider state
preference fit           <- verified place/preference match only
opportunity value        <- derived OpportunityWindow value only
```

If a metric has no verified input yet, mark it unavailable or use a formally documented neutral policy. Do not ask an LLM to manufacture it.

## Candidate families before OR-Tools

Implement small deterministic families first:

```text
F0 same-slot replacement
F1 optional activity removal
F2 suffix delay/shift
F3 opportunity-window-compatible replacement
```

Generate up to `candidate_count` distinct feasible candidate plans, pass each through the same authoritative gate, calculate verified scores, then present/rank them.

Only after this contract is stable should OR-Tools become another candidate generator/optimizer.

## OR-Tools role

OR-Tools may search a larger candidate space, but:

```text
OR-Tools output
-> persisted candidate representation
-> authoritative deterministic feasibility
-> verified scoring
-> ReplanDiff
```

The solver is never allowed to bypass the CityNexus gate.
