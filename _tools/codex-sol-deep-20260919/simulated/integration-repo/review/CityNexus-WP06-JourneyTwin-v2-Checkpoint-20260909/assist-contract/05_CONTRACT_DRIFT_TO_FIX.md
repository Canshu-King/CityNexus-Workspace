# API/state contract drift to close before frontend freeze

These are not reasons to stop the deterministic WP06 work, but they should be resolved before WP08 frontend contracts freeze.

## Replan generation

Current formal OpenAPI says:

- `trigger_event_id` required;
- `candidate_count` 1..5.

Runtime currently accepts a raw dict, makes trigger optional and ignores candidate_count.

Recommendation: introduce a typed `ReplanGenerateRequest` and make semantics explicit when multi-candidate WP06 is implemented.

## Replan acceptance idempotency

Formal OpenAPI requires `Idempotency-Key` on accept. Runtime currently does not.

Recommendation:

- add semantic idempotent re-accept behavior;
- require/validate the header before frontend freeze;
- repeated acceptance must not duplicate audit or state transitions.

## Proposal lifecycle

Use the declared lifecycle. For the synchronous API, generation may internally move `GENERATED -> PRESENTED` before returning to the client. Accept/reject then operate only on PRESENTED.

## Event lifecycle

Do not generate from RESOLVED/IGNORED events. Add acknowledgement/resolve transitions only when the UI needs them; do not invent extra states.
