# P7 Resolver Behavioral Receipt

Purpose: give lane C and Commander one exact, replayable receipt shape for `P7_RESOLVER_INTEGRATED` so symbol presence, grep hits, imports, or green unit counts cannot be mistaken for product integration.

This file does not add a new architecture gate. It mechanizes the already-frozen behavioral acceptance criteria.

## 1. Identity

Every delivery must record:

```text
delivery_sha
parent_sha
worktree_path
exact_test_or_replay_commands
normal_application_entrypoint
provider_module = PhotonIdentityProvider
product_consumer
receipt_generated_at
```

Commander upgrades nothing from a dirty/uncommitted worktree.

## 2. Four required behavioral receipts

All four outcomes must traverse the normal product/application path on the same exact SHA.

### MATCH

Required:

```text
input_raw
normalized_query
provider_outcome = MATCH
source_provider
source_entity_id
observed_at
wgs84_lat
wgs84_lon
extent_or_null
provider_attempts
canonical_destination_id
canonical_created_or_bound_by_server = true
pending_raw_key_used_as_canonical = false
malformed_provider_evidence = false
```

Hard negatives:

- if `source_provider` is missing -> do not mint a fallback/hash canonical id;
- if `source_entity_id` is missing -> do not mint a fallback/hash canonical id;
- if coordinates violate the typed WGS84 contract -> do not mint a fallback/hash canonical id;
- malformed MATCH evidence must become an explicit malformed/invalid-provider-evidence state.

### AMBIGUOUS

Required:

```text
provider_outcome = AMBIGUOUS
canonical_destination_id = null
candidate_count
candidate_source_ids
silent_selection = false
raw_preserved = true
normalized_query_preserved = true
provider_attempts
```

Replay must not silently pick a different candidate.

### NO_MATCH

Required:

```text
provider_outcome = NO_MATCH
canonical_destination_id = null
raw_preserved = true
pending_record_may_exist = true
pending_key_used_as_product_identity = false
semantic_response_parseable = true
semantic_result_count = 0
transport_contract_satisfied = true
provider_attempts
```

Hard negative:

A timeout, DNS failure, 401/403, 429, 5xx, malformed provider payload, or transport exception must not satisfy this receipt.

### RUNTIME_FAILURE

Required:

```text
provider_outcome = RUNTIME_FAILURE
canonical_destination_id = null
retryable_or_runtime_reason
raw_preserved = true
pending_key_used_as_product_identity = false
provider_attempts
collapsed_to_no_match = false
```

Replay/idempotency must not create a new pseudo-canonical identity.

## 3. ProviderAttempt audit invariant

The final product outcome and the audit history are different objects.

Every provider attempt must remain independently visible, including:

```text
provider
endpoint_or_mirror
attempt_index
started_at
finished_at
http_status_or_transport_error
semantic_parse_status
semantic_result_count_or_null
classification
```

Examples:

```text
A: timeout
B: semantic empty
=> final outcome may be NO_MATCH, but both attempts remain visible

A: 403
B: timeout
=> final outcome RUNTIME_FAILURE, both attempts remain visible
```

Never overwrite earlier attempt evidence with the last attempt.

## 4. Seven-condition P7 matrix

Commander must fill this matrix from behavior, not grep/import presence.

```text
1. previously-unseeded raw destination enters normal application path = PASS/FAIL
2. C consumes B typed ProviderResolution semantics in behavior = PASS/FAIL
3. exact raw and normalized query remain separate = PASS/FAIL
4. MATCH becomes server-owned canonical identity = PASS/FAIL
5. AMBIGUOUS / NO_MATCH / RUNTIME_FAILURE keep canonical=null = PASS/FAIL
6. operation/replay is persistent + idempotent = PASS/FAIL
7. pending/raw key never becomes product identity = PASS/FAIL
```

Only:

```text
all seven = PASS
```

permits:

```text
P7_RESOLVER_INTEGRATED = true
```

An import, grep hit, class construction, or unit test count is supporting evidence only.

## 5. Commander independent replay

Before changing P7:

1. reproduce from the exact delivered SHA;
2. run the declared four-outcome receipt suite;
3. inspect at least one persisted MATCH transition;
4. inspect at least one unresolved state with `canonical_destination_id=null`;
5. inspect full ProviderAttempt history for a multi-attempt case;
6. replay/idempotency check;
7. record the completed seven-condition matrix.

If any item is not directly verified:

```text
P7_RESOLVER_INTEGRATED = false
```

and the missing item is named.

## 6. Canary / Harness handoff

After P7 becomes true:

1. rebuild/restart canary from the exact P7 SHA;
2. issue a fresh canary identity receipt;
3. Commander smoke the visible unseen-destination path;
4. only then wake Harness + P1/P2/P3/P4;
5. findings from an older canary build are labeled `STALE_CANARY_OBSERVATION`.

## 7. Frozen rule

> P7 is a behavioral integration claim. Typed provider truth must survive the normal application path without semantic collapse, fabricated identity, or lost audit history.
