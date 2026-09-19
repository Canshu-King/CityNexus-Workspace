# Stay and mobility evidence

Runtime label: `CAPTURED_REPLAY_WITH_DETERMINISTIC_PLANNER`

## Multi-day Journey

The flagship request creates a Journey from Friday evening through Sunday afternoon with two travelers, occupancy `{adults: 2, rooms: 1}`, arrival at Tianjin West Station, departure at Tianjin Binhai Airport, and a CNY 700 total stay budget. The data is persisted in `journey_trip_contexts`; existing single-day Journeys remain valid because the context is additive.

## Accommodation contract

`CapturedAccommodationProvider` implements the same `AccommodationProvider` seam intended for a live adapter. Four immutable offers are captured with provider key `citynexus-captured-hotel` and provenance `CAPTURED_REPLAY`:

- Haihe Riverside Hotel: CNY 360 total, refundable.
- Central Station Courtyard: CNY 420 total, refundable.
- Five Avenues House: CNY 520 total, refundable.
- North Canal Guesthouse: CNY 310 total, non-refundable.

Each snapshot persists nightly amount, total, taxes, explicit CNY currency, room type, occupancy, check-in/out, cancellation rule, capture time, expiry, provider, and evidence confidence. The UI labels these as planning evidence and does not imply that a booking or payment occurred.

## Mobility contract

The captured matrix covers WALK, BICYCLE, TRANSIT, AUTO, and RIDE_HAIL for the Tianjin destinations. WALK deliberately carries `cost_amount_minor=null` and `cost_status=UNKNOWN`; known captured modes carry explicit CNY cost evidence. Provider status is visible in the experience payload: captured mobility is ready, while Valhalla and live transit are `NOT_CONFIGURED`.

## Ranking and solver

Each bounded hotel candidate is evaluated with its own mode facts. The mode-aware CP-SAT layer chooses one feasible mode per leg and considers time, captured cost, walking, transfers, weather exposure, reliability, and soft TravelerTwin preference. Protected arrival/departure margins remain hard business facts. The API exposes stay total, daily travel, mobility total, walking, protected margin, arrival/departure fit, cancellation score, optimizer kind, weather state, and a Journey-impact explanation.

## Recovery evidence

`POST /api/v1/journeys/{journey_id}/stay-options/{option_id}/autopilot/recover` sends a RAIN signal through the existing Delegation Policy. In the V8 test, an AUTONOMOUS policy with a CNY 50 cost envelope and 20-minute drift envelope executes the reversible transport switch to TRANSIT, re-generates the stay-aware option, records a provider-verified event and audit decision, and returns `post_action_gate=PASSED` with protected commitments preserved. The default ADVISORY policy returns `REQUIRE_CONFIRMATION` and does not mutate the option.

