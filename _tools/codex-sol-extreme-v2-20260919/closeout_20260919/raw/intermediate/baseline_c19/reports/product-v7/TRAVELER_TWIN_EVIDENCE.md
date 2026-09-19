# TravelerTwin V7 Evidence

## Persisted projection

CityNexus persists:

- explicit `Preference` rows as `EXPLICIT` evidence;
- append-only `JourneyOutcomeEvent` rows for actual Activity transitions and user/Agent decisions;
- decayable `TravelerPreferenceEvidence` rows as `LEARNED_SOFT` evidence;
- a materialized `TravelerTwinSnapshot` for inspection and planning.

The inspection response exposes explicit preferences, learned direction/strength/confidence, evidence count, source, explanation, Journey IDs, last observed time, expiry, conflicts, and provenance. `DELETE /api/v1/travelers/{traveler_id}/traveler-twin/learned` clears learned evidence while retaining explicit preferences.

## Flagship cross-Journey proof

1. Journey A records actual starts, skips, and completions. Reflect processing extracts bounded indoor evidence from those outcomes.
2. Journey B uses the same Traveler. The learned indoor signal measurably ranks indoor/cultural candidates above outdoor candidates, then a predictive risk crosses the resilience threshold. Guardian invokes the server Gateway and CP-SAT-backed recovery autonomously within the policy envelope while preserving the protected cruise/C4 activity.
3. Journey C contains an explicit outdoor mission. Mission-local explicit evidence wins, learned indoor evidence is suppressed for that Journey, and the global Agent policy remains unchanged.

As stretch coverage, a second cross-Journey test records an actual accepted outcome with a low-walking preference signal. Reflect learns `low_walking` as a separate soft dimension; later planning utility prefers candidates tagged `low_walking` without changing the Traveler's loss or autonomy envelope.

The backend flagship test asserts persisted outcome evidence, TravelerTwin learning, ranking difference, autonomous recovery, protected commitment preservation, trace spans, captured replay, clearability, and no authority escalation. The frontend Control Tower test asserts that persisted evidence and the authority boundary are visible after reload.

## Safety boundary

TravelerTwin contributes soft planning utility and explanations only. Learned evidence cannot increase budget, payment, booking, Commitment, schedule-drift, provider, or autonomy authority. Explicit mission intent can override learned soft preference locally without mutating the global envelope.
