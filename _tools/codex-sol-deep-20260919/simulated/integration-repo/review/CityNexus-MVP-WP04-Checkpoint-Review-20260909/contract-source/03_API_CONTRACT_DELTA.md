# WP04 API Contract Delta

The original blueprint already contains create booking, cancel booking, create order and create transaction. WP04 requirements reveal several missing contract operations/guards.

## Existing endpoints to implement

```text
POST /api/v1/journeys/{journey_id}/bookings
POST /api/v1/bookings/{booking_id}/cancel
POST /api/v1/journeys/{journey_id}/orders
POST /api/v1/journeys/{journey_id}/transactions   [Idempotency-Key required]
```

## Add before claiming IR-006/IR-007 complete

```text
GET /api/v1/city-services/{service_id}/booking-slots
GET /api/v1/bookings/{booking_id}
GET /api/v1/transactions/{transaction_id}
```

Why:
- IR-006 explicitly requires availability, create, cancel and status operations.
- IR-007 requires payment initiation and final status query.
- FR-032 requires normalized bookable slots with provider provenance.

These may remain a small WP04 extension; do not redesign the rest of the API.

## Request validation additions

### BookingCreate

- `activity_id` required.
- `provider_key` defaults to `mock-booking`.
- client cannot submit price, provider confirmation, external ref or commitment strength.

Server derives price and schedule from selected Activity/provider data.

### OrderCreate

- `activity_id` required.
- `items` >= 1.
- server recomputes total from validated input/service fixture.
- fulfillment window may be derived from the linked Activity start/end for the MVP.

### TransactionCreate

Require exactly one of:

```text
booking_id XOR order_id
```

Guards:
- target belongs to same Journey;
- amount/currency match authoritative target for AUTHORIZE/CAPTURE;
- no client payment credential fields exist;
- provider_key must be a configured adapter.

## Response semantics

### Booking create provider success

`201` + Booking with `CONFIRMED`, external_ref, commitment_id.

### Booking provider rejection

Prefer `201` + persisted Booking with `FAILED` and no ACTIVE confirmed commitment. This records the attempt while making the failure explicit. If Codex chooses a controlled 422 instead, it must still satisfy FR-033 evidence and provider-call audit; do not return a false CONFIRMED record.

### Transaction first execution

`201` + new Transaction.

### Idempotent replay

Recommended: `200` + same Transaction logical result, no new provider call, no new transaction, no second commitment strengthening.

If retaining `201` for compatibility, tests must still prove no duplicate side effect. Update OpenAPI to document whichever policy is chosen.

### Same idempotency key, different semantic request

`409 IDEMPOTENCY_CONFLICT` before provider call.

### Provider payment failure

Persist explicit `FAILED` PaymentTransaction; commitment is not upgraded to paid/anchored state.

## Receipt traceability

Successful PaymentTransaction response must include `external_ref` (mock receipt/provider transaction reference). This supplies the WP04 basis for FR-038; Journey history UI can surface it later.

## Order input correction before implementation

The blueprint `OrderCreate` currently accepts `unit_amount_minor` from the client. Do not use that as authoritative price. Preferred WP04 contract:

```json
{"activity_id":"...","items":[{"sku":"local-lunch-box","quantity":1}]}
```

Server resolves SKU/unit price from the deterministic commerce catalog and computes the total. If the existing field is retained for backwards compatibility, ignore it for pricing and return the authoritative priced lines.

## Refund/void scope

The existing transaction enum includes REFUND/VOID, but the current request does not identify an original transaction unambiguously. Do not invent ambiguous refund logic merely to make an enum look complete. WP04 Golden Scenario requires CAPTURE + final status query. Keep FR-037 conservative/PARTIAL until a traceable refund design is implemented and tested.
