# Graceful degradation contract

CityNexus must fail honestly. Cached evidence is usable only with its provenance, freshness and operation scope intact.

- Routing timeout, 5xx or malformed JSON: return controlled unavailability; never synthesize an ETA or geometry. Hard replanning rejects synthetic fallback.
- Places timeout: retain existing confirmed places if still valid; do not present absence of results as proof a venue does not exist.
- Duplicate/alias identity: compare canonical physical identity. Ambiguous identity remains ambiguous and cannot be upgraded to SAME.
- AI unavailable, slow or malformed: use a declared deterministic fallback where supported, otherwise expose degradation. Never parse partial prose into authoritative structured truth.
- Booking import partial/malformed: validate or quarantine atomically; never create duplicate commitments or silently confirm an incomplete reservation.
- Offline frontend: render the saved snapshot with freshness and read-only limits. Financial and irreversible actions remain disabled.
- Stale session/proposal: reject with conflict and require refresh/regeneration; never apply against a different active base plan.
- Map failure: preserve itinerary text and evidence controls; show unavailable/empty state, never a fabricated route line.
- Duplicate actions: replay identical idempotent responses; reject same-key/different-request; do not duplicate audit/commitment mutations.

Required evidence per failure: provider/error class, operation key, request correlation or idempotency key, cache/freshness decision, and whether any fallback was used. Secrets and raw tokens are excluded.

