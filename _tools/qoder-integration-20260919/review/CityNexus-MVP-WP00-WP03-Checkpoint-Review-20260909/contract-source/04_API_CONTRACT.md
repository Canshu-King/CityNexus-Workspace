# 04 - API Contract

Canonical machine-readable contract: `api/openapi.yaml`.

Base path: `/api/v1`

## Endpoint groups

### System / demo
- `GET /health`
- `POST /demo/reset`
- `POST /demo/scenarios/disruption`

### Traveler/preferences
- `POST /travelers`
- `GET /travelers/{traveler_id}`
- `GET /travelers/{traveler_id}/preferences`
- `PUT /travelers/{traveler_id}/preferences`

### Journey/constraints
- `POST /journeys`
- `GET /journeys/{journey_id}`
- `PATCH /journeys/{journey_id}`
- `GET /journeys/{journey_id}/constraints`
- `POST /journeys/{journey_id}/constraints`
- `DELETE /journeys/{journey_id}/constraints/{constraint_id}`

### Discovery and planning
- `GET /places`
- `GET /city-services`
- `POST /journeys/{journey_id}/plans/generate`
- `GET /journeys/{journey_id}/plans`
- `GET /plans/{plan_version_id}`
- `POST /journeys/{journey_id}/plans/{plan_version_id}/select`

### Commerce
- `POST /journeys/{journey_id}/bookings`
- `POST /bookings/{booking_id}/cancel`
- `POST /journeys/{journey_id}/orders`
- `POST /journeys/{journey_id}/transactions`

### Execution / twin
- `POST /journeys/{journey_id}/start`
- `POST /journeys/{journey_id}/activities/{activity_id}/complete`
- `GET /journeys/{journey_id}/twin`
- `GET /journeys/{journey_id}/history`

### Events and replanning
- `POST /journeys/{journey_id}/events`
- `GET /journeys/{journey_id}/events`
- `POST /journeys/{journey_id}/replans`
- `GET /journeys/{journey_id}/replans`
- `GET /replans/{proposal_id}`
- `POST /replans/{proposal_id}/accept`
- `POST /replans/{proposal_id}/reject`

### AI Copilot
- `POST /journeys/{journey_id}/copilot/messages`

## Write semantics

- All request bodies are JSON.
- Transaction creation and proposal acceptance require `Idempotency-Key`.
- `409` is used for stale state/version conflicts.
- `422` is used for validation or hard-constraint failures where the request is syntactically valid but semantically infeasible.
- Replan proposal acceptance fails if `journey.active_plan_version_id != proposal.base_plan_version_id`.

## Compatibility rule

Frontend must consume the OpenAPI contract rather than re-inventing response shapes. If implementation changes an API shape, update `api/openapi.yaml` in the same change.
