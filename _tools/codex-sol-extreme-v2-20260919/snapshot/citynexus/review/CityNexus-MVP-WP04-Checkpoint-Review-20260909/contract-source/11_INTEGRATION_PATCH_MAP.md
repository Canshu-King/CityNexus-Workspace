# WP04 integration patch map against the current checkpoint

This file exists so Codex does not have to rediscover where each change belongs.
Apply only after the current pre-WP04 WP03 repair gate is green.

## Low-conflict mechanical scaffold

Run:

```powershell
python <assist>\tools\apply_wp04_scaffold.py D:\moodle\CityNexus D:\moodle\CityNexus\domain-model\<current-v0.4.2-yaml>
```

The helper performs only low-conflict work:

- reads the exact source `C0..C4` strength list and refuses ambiguity;
- generates `backend/app/commerce/strengths_generated.py`;
- changes the empty pre-WP04 `commitments.level` SQL CHECK to the exact five codes;
- changes the OpenAPI Commitment enum to the exact five codes;
- adds ORM classes for Commitment/Booking/Order/PaymentTransaction/ProviderCall/IdempotencyKey;
- adds commerce Pydantic schemas;
- copies pure policy/idempotency/validation/provider modules;
- adds pure reference tests.

It deliberately **does not** add HTTP endpoints or alter WP03 feasibility code.

The script is idempotent at the source-file level. In a synthetic fresh copy of the current checkpoint it was applied twice and the combined suite remained green.

## Manual integration locations after scaffold

### `backend/app/main.py`
Add route functions only. Keep orchestration out of the route body.

Required WP04 endpoints:

```text
GET  /api/v1/city-services/{service_id}/booking-slots
POST /api/v1/journeys/{journey_id}/bookings
GET  /api/v1/bookings/{booking_id}
POST /api/v1/bookings/{booking_id}/cancel
POST /api/v1/journeys/{journey_id}/orders
POST /api/v1/journeys/{journey_id}/transactions
GET  /api/v1/transactions/{transaction_id}
GET  /api/v1/commitments/{commitment_id}   # small demo/inspection endpoint
```

Do not place strength derivation or provider-authority decisions in `main.py`.

### `backend/app/commerce/service.py` (new)
Implement SQLAlchemy orchestration here. Recommended methods:

```text
get_booking_slots
create_booking
get_booking
cancel_booking
create_order
create_transaction
get_transaction
get_commitment
```

For every write, perform all validation before provider/domain mutation where possible.

### `backend/app/db/models.py`
The mechanical scaffold appends the six ORM classes because the SQL tables already exist. Do not create second tables with new names.

### `backend/app/schemas.py`
The mechanical scaffold appends Booking/Order/Transaction/Commitment/BookingSlot schemas. Adapt fields to the final OpenAPI rather than inventing parallel DTOs.

### `backend/app/integrations/commerce_ports.py`
Use the supplied port signatures. IR-006 requires booking availability/create/cancel/status. IR-007 requires payment initiation plus status query.

### `backend/app/integrations/mock/commerce_providers.py`
Use deterministic provider outcomes. No randomness, no network, no credentials.

### `backend/app/commerce/commitment_policy.py`
Keep policy pure. Persist both exact source code and numeric rank/evidence. Payment alone must not imply C4.

### `backend/app/commerce/idempotency.py`
The legacy DB column is called `request_hash`, but the MVP may store the canonical request signature there. This is application idempotency, not package/file hash work.

### `backend/db/schema.sql`
Only the existing commitments strength CHECK needs source-enum reconciliation in WP04A. The booking/order/transaction/provider/idempotency tables already exist.

### `contracts/openapi.yaml`
Merge `contracts/openapi_wp04_delta.yaml` and exact source strength enum. Do not claim IR-006/IR-007 complete until status/availability query operations exist.

## Do not touch

- frozen domain/requirements sources except one read-only enum lookup;
- Visio renderer;
- frontend;
- WP05/WP06 state transitions;
- real payment/booking APIs;
- AI;
- package/file hash bookkeeping.
