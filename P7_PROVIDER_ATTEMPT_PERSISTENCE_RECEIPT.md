# P7 ProviderAttempt Persistence Receipt

Purpose: close the remaining audit-evidence ambiguity for P7 without forcing internal attempt history into the public capability response.

## 1. Public response is not the audit store

`GET /api/v1/destinations/capability` does NOT need to expose every ProviderAttempt to the client.

What P7 requires is that the same normal application request can be tied to durable, structured, retrievable attempt history.

Therefore this is acceptable:

```text
capability response: no attempt array
operation/audit store: complete ProviderAttempt[] retrievable by correlation/operation key
```

This is NOT acceptable:

```text
capability response: no attempt array
attempt history only exists in ephemeral logs / debugger memory / test fixture
```

## 2. Required persistence receipt

Lane C must provide, for the exact candidate SHA:

```text
product_sha
normal_application_entrypoint
input_raw
normalized_query
request_or_operation_id
attempt_store_kind
attempt_store_location
association_key
ordering_key
retrieval_command
retrieved_attempt_count
retrieved_attempts
final_provider_outcome
final_product_reason
```

`attempt_store_location` should name the durable structured location, for example:

```text
table.column
operation.metadata_json.provider_attempts
audit_event.payload.provider_attempts
```

Do not answer only with a Python symbol name.

## 3. Retrieval proof

Commander must independently run the supplied retrieval command against the exact-SHA test/canary database and show that:

- the association key resolves the same request/operation;
- attempts are ordered deterministically;
- all attempts are present, not only the last one;
- provider/mirror, transport result, semantic parse/result count, and classification are preserved;
- the final typed outcome can be explained from the attempt history.

## 4. Required behavioral witnesses

### MATCH

Receipt must tie:

```text
ProviderAttempt[]
-> chosen source_provider/source_entity_id
-> valid WGS84 evidence
-> server-owned canonical identity
```

### NO_MATCH

At least one completed provider path must show a parseable semantic empty response under a satisfied transport/protocol contract.

A timeout, DNS error, 401/403, 429, 5xx, malformed payload, or transport exception cannot by itself justify NO_MATCH.

### RUNTIME_FAILURE

Attempt history must retain the runtime/access/transport failure and the product result must remain runtime/retryable, not collapse to NO_MATCH.

### Multi-attempt example

```text
A -> timeout
B -> semantic empty
final outcome -> NO_MATCH
```

Both A and B must remain retrievable.

## 5. Durability / replay check

For at least one case:

1. perform the normal application request;
2. retrieve ProviderAttempt history;
3. close/reopen the application DB session or restart the test process;
4. retrieve by the same durable association key;
5. confirm the same logical attempt history is still present;
6. replay/idempotency must not create a second pseudo-canonical identity.

If attempt evidence disappears after process memory is gone, P7 condition 6 is not proven.

## 6. P7 gate implication

Missing attempts from the public capability JSON is NOT itself a P7 failure.

The actual gate question is:

> Can Commander independently retrieve complete structured ProviderAttempt history for the exact normal-path request from durable product evidence, and does that history support the typed outcome without semantic collapse?

Until the answer is yes, P7 stays false.
