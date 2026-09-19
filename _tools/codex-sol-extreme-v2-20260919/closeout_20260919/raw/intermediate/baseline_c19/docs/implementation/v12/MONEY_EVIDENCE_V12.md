# V12 Money Evidence

Money is represented as integer minor units with an explicit status on bookings and commitments.

Allowed statuses are `FREE_KNOWN`, `KNOWN`, `ESTIMATED`, and `UNKNOWN`. Unknown is a first-class provider state; it is not serialized as zero and is not treated as free. V12 composition rejects a POI whose cost cannot be evidenced and includes stay, activity, and mobility costs in the deterministic budget gate. Autonomous recovery keeps `cost_delta_minor`, `loss_delta_minor`, and provider degradation in the authorization facts.
