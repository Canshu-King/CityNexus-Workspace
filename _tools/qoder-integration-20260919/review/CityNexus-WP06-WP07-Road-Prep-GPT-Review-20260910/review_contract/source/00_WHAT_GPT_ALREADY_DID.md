# What GPT Already Did for Codex

This package is intentionally implementation-heavy so Codex does not spend another long cycle rediscovering the same issues.

## Directly implemented and validated

- fixed `candidate_count` semantics to stop after N **feasible** candidates;
- implemented weighted persisted Traveler interest preference matching;
- removed fabricated duration-based Opportunity score;
- filtered completed/past active commitments out of JourneyTwin `upcoming_commitments`;
- added optional generation idempotency with safe replay/conflict behavior;
- removed UUID4 tie-breaking from best-candidate selection;
- created real Opportunity Window evaluation reference code;
- created provider-verified weather snapshot/evidence reference code;
- created deterministic verified candidate-ranker boundary suitable for later OR-Tools output;
- created typed Copilot context/action boundary forbidding direct AI state mutation;
- added five WP06 follow-up regression tests and four WP07 foundation tests;
- validated the patch on a fresh copy of the supplied checkpoint.

## Intentionally not pretended complete

- F3 is not wired into the live generator by this patch. The reference evaluator is ready, but Codex must integrate it against current active-plan/C4/provider facts.
- Open-Meteo is not turned on as a mandatory network service.
- Valhalla is not made mandatory.
- OR-Tools is not installed or made authoritative.
- DeepSeek credentials are not included.
- Frontend is not generated against an unstable API contract.

That separation is deliberate. Infrastructure should not become “implemented” merely because a file with the right noun exists.
