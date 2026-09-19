# V15 Copilot Intent Contract

## Request routing

`POST /api/v1/journeys/{journey_id}/copilot/messages` accepts `message` and an optional `locale` (`en` or `zh`). The server builds read-only verified context before interpretation. DeepSeek, when configured, must return the JSON schema in `app/integrations/ai/copilot_contract.py`; otherwise the deterministic classifier supplies the same vocabulary.

The server confirms current-event language before allowing `DISRUPTION_REPORT`. A conditional phrase such as “What if it rains?” or “如果下雨会怎样？” is never an event. A preference such as “If it rains, take transit” is `PREFERENCE_CHANGE`. Only current, known disruption language can create `CLOSURE`, `TRAFFIC_DELAY`, `SCHEDULE_DELAY`, or `WEATHER`.

## Response

Every response includes:

- `intent`: name, confidence, reason, entities, provider, and `AI`/`FALLBACK` mode;
- `action`: an explicit request action only (`REQUEST_REPLAN`, `REQUEST_PREFERENCE_UPDATE`, `REQUEST_PLAN_EXPLANATION`, or `REQUEST_PLACE_SEARCH`);
- `what_if`: a structured read-only simulation or an honest unavailable result;
- `protected_commitments` and `evidence` from server-owned facts;
- `event` only for a confirmed current disruption report.

## Authority boundary

DeepSeek may interpret meaning, ambiguity, and traveler intent. It cannot authoritatively invent Activity IDs, coordinates, prices, route times, opening hours, commitments, provider status, or mutations. Deterministic CityNexus code owns those facts and the action path.

Non-disruption branches do not call `_twin_snapshot`, do not create a JourneyTwin projection, and do not commit a session. The disruption branch writes only the explicit `USER_REPORTED` Event and audit record; recovery remains on the existing Guardian/replan path.
