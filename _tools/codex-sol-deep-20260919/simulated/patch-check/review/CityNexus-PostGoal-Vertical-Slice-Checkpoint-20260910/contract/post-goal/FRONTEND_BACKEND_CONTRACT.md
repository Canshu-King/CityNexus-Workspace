# Frontend ↔ Backend Golden Scenario Contract

## Domain ownership

Backend is authoritative for:

```text
Journey
PlanVersion
Activity
Booking
Transaction
Commitment
Event
ReplanProposal
Feasibility
JourneyTwin
Provider evidence
```

Frontend may own only transient UI/workflow state.

## Storage rule

Allowed browser persistence examples:

```text
journey_id for reconnect
UI density/theme preference
last open tab
```

Forbidden as domain truth:

```text
accepted plan flag
hard-coded C4 list
hard-coded feasibility result
hard-coded replan score/diff
hard-coded provider status
```

A reload must recover business state by querying backend.

## Golden Scenario HTTP flow

Minimum flow already exercised by the backend contract test:

```text
POST /api/v1/demo/reset
POST /api/v1/journeys/{journey_id}/plans/generate
POST /api/v1/journeys/{journey_id}/plans/{plan_id}/select
POST /api/v1/journeys/{journey_id}/bookings
POST /api/v1/journeys/{journey_id}/transactions
POST /api/v1/journeys/{journey_id}/start
GET  /api/v1/journeys/{journey_id}/twin
POST /api/v1/journeys/{journey_id}/events
POST /api/v1/journeys/{journey_id}/replans
GET  /api/v1/journeys/{journey_id}/replans
POST /api/v1/replans/{proposal_id}/accept
GET  /api/v1/journeys/{journey_id}/twin
```

Use the actual current OpenAPI schema as authority if signatures evolve.

## Render contract

Journey Mode should map backend data to UI evidence:

```text
JourneyTwin.current_activity_id
JourneyTwin.upcoming_commitments
JourneyTwin.context.opportunity_window
JourneyTwin.context.feasibility_envelope
JourneyTwin.context.provider_level / degraded_providers
ReplanProposal.diff
ReplanProposal.score_breakdown
ReplanProposal.explanation
```

Do not fabricate placeholder values once the backend path exists. Loading/error/degraded states are preferable to pretend certainty.

## XState boundary

XState should orchestrate actions such as:

```text
bootstrapping
ready
generatingReplan
comparing
accepting
rejecting
error
```

It must not duplicate the backend Journey/Plan/Replan state machine as a second source of truth.
