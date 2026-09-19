# JourneyTwin v2 — next projection work

The current Twin exists but its `context` only exposes Journey status. The already-installed OpportunityWindow and FeasibilityEnvelope modules are not wired into runtime yet.

## Twin remains a projection

Do not move authority into JourneyTwin. It is rebuilt from:

- Journey;
- active PlanVersion/Activities;
- current execution position;
- Commitments;
- Events;
- frozen provider/context facts.

## Add derived context

Suggested `context` payload:

```json
{
  "journey_status": "ACTIVE",
  "provider_level": 1,
  "degraded_providers": [],
  "feasibility_envelope": {
    "next_commitment_buffer_min": 52,
    "journey_end_slack_min": 30,
    "budget_remaining_minor": 13000,
    "preserved_commitment_count": 1,
    "risk_reason_codes": []
  },
  "opportunity_window": {
    "opens_at": "...",
    "must_depart_by": "...",
    "available_minutes": 47,
    "next_commitment_start": "..."
  }
}
```

Inject demo `now` explicitly. Never calculate a 2026-10-10 Journey against the workstation's real wall-clock date during deterministic tests.

## Persistence rule

A projection update caused by a state-changing command must be committed in the same transaction as that command. A GET may rebuild/refresh, but it must not be the only way Twin becomes durable.
