# V12 Frozen Provider Evidence

V12 treats provider capture as an input to planning, never as a hidden side effect of validation.

- `PlanVersion.mobility_snapshot_id` identifies the immutable provider world used to compose the candidate.
- `PlanVersion.mobility_evidence_json` stores the complete directed node matrix, selected leg facts, provider/provenance, capture and expiry timestamps, route geometry, cost status, and stay evidence.
- Selection reconstructs `MobilitySnapshot` from the persisted evidence and runs the deterministic gate against that snapshot. It does not recapture mobility.
- Replan replays the selected V12 evidence first; selected leg facts override matrix alternatives for the original route, while the full matrix remains available for bounded Trip Studio edits.
- Provider degradation is explicit in the evidence and cannot silently become a successful provider claim.

The authoritative boundary is therefore: capture → freeze → plan → deterministic post-action gate. Natural-language interpretation may identify a disruption, but it does not replace the frozen business facts.
