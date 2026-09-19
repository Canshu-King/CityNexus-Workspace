# V15 What-If Evidence

## Contract

What-If responses carry `simulation_only: true` and a `READ_ONLY_SIMULATION` provenance label. The result is computed from the selected PlanVersion's persisted Activity and JourneyLeg facts plus server-owned commitments. It never selects a plan, refreshes JourneyTwin truth, weakens a Commitment, creates a Booking, captures a Payment, or records a reality Event.

The result includes:

```json
{
  "simulation_only": true,
  "status": "SIMULATED | BLOCKED | NEEDS_LIVE_EVIDENCE | NOT_SIMULATABLE_FROM_CURRENT_EVIDENCE",
  "feasibility": "PASS | BLOCKED | UNKNOWN",
  "before": {},
  "after": {},
  "deltas": {"cost_minor": 0, "walking_min": 0, "schedule_drift_min": 0},
  "affected_activities": [],
  "protected_commitments": {"count": 0, "preserved": true, "ids": []},
  "proposed_changes": [],
  "provenance": {"mode": "READ_ONLY_SIMULATION"},
  "explanation": "...",
  "next_action": "REQUEST_REPLAN"
}
```

## Proven scenarios

- Extending a flexible Activity by 30 minutes can return `SIMULATED`/`PASS` when the next protected window remains feasible; the only next step is an explicit replan request.
- Extending a locked Activity returns `BLOCKED`; the response leaves the selected plan unchanged.
- Cost, reduced walking, indoor alternatives, or a hypothetical weather/closure path returns `NEEDS_LIVE_EVIDENCE` when the current plan does not contain the provider facts needed to prove the alternative.
- A generic Fuzhou Journey with no selected PlanVersion returns `NOT_SIMULATABLE_FROM_CURRENT_EVIDENCE` instead of borrowing Tianjin data.
- “如果下雨会怎样？” returns `WHAT_IF` with no Event; “现在堵车了” returns `DISRUPTION_REPORT` and one `USER_REPORTED` Event.

## UI evidence

`output/playwright/v15-tianjin-copilot-what-if.png` shows a selected sealed Tianjin PlanVersion preview with before/after cost and walking metrics, `SIMULATION ONLY`, deterministic fallback provenance, and `BLOCKED` feasibility for a protected/locked current Activity. The browser console had zero errors after the updated backend service was loaded.
