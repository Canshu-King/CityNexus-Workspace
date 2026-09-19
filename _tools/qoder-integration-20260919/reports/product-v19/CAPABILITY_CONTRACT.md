# Capability Contract

Canonical codes are `STEP_FREE_REQUIRED`, `AVOID_STAIRS`, `MAX_WALKING_PER_LEG_M`, `MAX_CONTINUOUS_WALKING_MIN`, `MAX_DAILY_WALKING_M`, `MIDDAY_REST_WINDOW`, `REST_EVERY_MIN`, `INFANT_NAP_WINDOW`, `TOILET_BREAK_EVERY_MIN`, `STROLLER`, `LARGE_LUGGAGE`, `SLOW_PACE`, `QUIET_ENVIRONMENT`, `INDOOR_PREFERRED`, and `SENSORY_LOW_STIMULATION`.

Every record carries class, severity (`HARD`, `STRONG`, `SOFT`), scope (`TRAVELER` or `JOURNEY`), params, source, provenance, explicit, confirmed, and active state. Hard durable facts require the explicit `/confirm` action. A plain replacement request returns `409` for unconfirmed hard needs.

Behavioral learning only populates `LEARNED_SOFT` preference evidence. It never writes `TravelerCapability` hard records.
