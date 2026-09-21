# P7 Check Validator Calibration

Purpose: prevent the P7 validator itself from becoming a one-sided gate that is excellent at rejecting bad receipts but accidentally rejects good ones or drifts away from the receipt contract.

## 1. Two-sided calibration is mandatory

Before Commander treats `p7_check.py` as a release gate, prove both directions on the same validator version:

- one fully compliant positive receipt -> `exit=0`, `P7=true candidate`;
- each negative mutation -> `exit=1`, with the expected named rejection reason.

A validator that only demonstrates rejection has not yet proved that the acceptance path is reachable.

## 2. Mutation corpus

Create all negative cases by mutating the known-good positive receipt one invariant at a time. Minimum mutations:

1. symbol/import-only evidence with no normal application path;
2. test-count-only evidence;
3. grep-hit-only evidence;
4. MATCH missing `source_provider`;
5. MATCH missing `source_entity_id`;
6. MATCH invalid or absent WGS84;
7. MATCH fabricates hash/pending canonical identity;
8. AMBIGUOUS silently selects a candidate;
9. AMBIGUOUS produces canonical identity;
10. NO_MATCH produced from timeout/transport failure;
11. NO_MATCH produced from 401/403/429/5xx;
12. NO_MATCH without parseable semantic empty response;
13. RUNTIME_FAILURE collapsed to NO_MATCH;
14. unresolved outcome produces pseudo-canonical identity;
15. only final ProviderAttempt retained;
16. replay changes canonical/candidate semantics;
17. self-declared seven-condition PASS without underlying behavioral evidence.

Each mutation should fail for the intended invariant, not merely because some unrelated field also became invalid.

## 3. Acceptance witness

The positive receipt should contain a minimal but complete behavioral witness for all four typed outcomes on one exact SHA:

```text
MATCH
AMBIGUOUS
NO_MATCH
RUNTIME_FAILURE
```

and a completed seven-condition matrix whose PASS values are derived from those witness sections.

## 4. Validator identity

Every validator result should record:

```text
validator_sha
receipt_schema_version
receipt_sha256
product_sha_under_test
exit_code
named_rejections
```

This prevents a morning report from citing a receipt that was checked by a different validator revision.

## 5. Contract drift rule

`P7_RESOLVER_BEHAVIOR_RECEIPT.md`, the JSON receipt format, and `p7_check.py` must share one version identifier.

If any required field or semantic rule changes, bump the receipt schema version and rerun both:

- positive control;
- full negative mutation corpus.

Do not maintain two separate lists of required semantics by hand if they can be generated from one source.

## 6. Frozen rule

> A fail-closed gate must prove that valid evidence can pass, not only that invalid evidence can fail.
