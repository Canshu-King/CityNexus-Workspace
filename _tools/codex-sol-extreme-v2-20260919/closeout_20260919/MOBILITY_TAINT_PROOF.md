# Mobility Truth Taint Proof — Closeout Carry-Forward

This closeout did not alter the accepted mobility truth implementation.

Static proof retained by the final candidate and current Qoder line:

- hard feasibility admits only `EXPLICIT_FROZEN_FIXTURE` and `LIVE_PROVIDER_CAPTURE`;
- unknown or absent `fact_quality` is not hard evidence;
- hard capture configures no mock fallback;
- provider provenance and fact quality survive capture, normalization, evidence, candidate, replan, and projection boundaries;
- physical identity uses the dedicated comparator and does not equate null IDs, coordinate-only similarity, or cross-provider numeric IDs.

Dynamic proof:

- focused Qoder truth contracts: 65 passed;
- mutation campaign killed provenance laundering, `None`-as-hard, mock hard fallback, and three unsafe physical-identity mutations;
- full backend regression: 832 passed, 0 failed.

Merge recommendation: retain the current Qoder mobility/identity implementation. Only port the narrow cursor, serialization, and C4 uniqueness changes around it.
