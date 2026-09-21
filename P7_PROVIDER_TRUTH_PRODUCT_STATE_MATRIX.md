# P7 Provider Truth -> Product State Matrix

Purpose: bind provider evidence truth to product identity/capability/action so the same `canonical=null` shape cannot be misclassified in opposite directions.

This is not a new architecture layer. It is the decision table for the already reproduced bugs:

- `answered=false` but product says `HYDRATABLE / START_HYDRATION`;
- `answered=true` with malformed identity evidence but product says `provider_no_match / NO_CANONICAL_IDENTITY`.

## 1. Separate the dimensions

Do not derive product truth from `canonical_destination_id is null` alone.

Track these dimensions separately:

```text
provider_evidence_state
canonical_identity_state
capability_state
recommended_action
retryability
audit_history
```

The same `canonical=null` can mean ambiguity, semantic no-match, runtime failure, malformed evidence, or not-attempted resolution. Those are not interchangeable product truths.

## 2. Decision matrix

| Provider evidence | Minimum evidence shape | Canonical identity | Product capability semantics | Action semantics | Retryable | Forbidden collapse |
| --- | --- | --- | --- | --- | --- | --- |
| VALID_MATCH | answered=true, parseable candidate, provider/entity id, valid WGS84 | server-owned canonical | coverage-driven: may become HYDRATABLE or another valid canonical-backed state | hydration only if coverage says HYDRATABLE | depends on later stage | must not become unresolved/hash |
| AMBIGUOUS | answered=true, >=2 plausible valid candidates | null | disambiguation-needed / unavailable-for-planning | ask user to disambiguate/select/refine | usually user-actionable | must not silently choose first; must not hydrate |
| SEMANTIC_NO_MATCH | transport/protocol satisfied, parseable semantic empty result | null | unavailable/no-result | refine/change destination | usually not runtime-retry | must not be inferred from timeout/403/5xx/malformed |
| RUNTIME_FAILURE | provider did not successfully answer: timeout/DNS/refused/401/403/429/5xx/transport error | null | retryable resolver-unavailable/unknown, NOT HYDRATABLE | retry later / retry resolver | yes | must not become NO_MATCH; must not hydrate |
| MALFORMED_EVIDENCE | provider answered, payload parseable enough to contain candidate-like data, but required identity evidence is invalid/missing | null | retryable provider-evidence/contract failure, NOT HYDRATABLE | retry later / provider issue path | yes | must not become NO_MATCH or NO_CANONICAL_IDENTITY-as-structural-absence; must not fabricate identity |
| NOT_ATTEMPTED / DISABLED | provider path not actually attempted | null unless local identity already exists | configuration/not-attempted truth; NOT evidence of no-match | configured recovery path | depends on cause | must not claim provider answered/no-result |

Public enum names may reuse existing states when semantics are already correct. Do not create new public enums merely to satisfy this document. The semantic distinctions must still be retained in structured reason/audit data.

## 3. Two hard product invariants

### Identity prerequisite for hydration

```text
capability == HYDRATABLE
=> trustworthy canonical identity exists
```

and:

```text
recommended_action == START_HYDRATION
=> capability == HYDRATABLE
=> trustworthy canonical identity exists
```

Therefore all of the following must be impossible:

```text
answered=false + canonical=null + HYDRATABLE
RUNTIME_FAILURE + canonical=null + START_HYDRATION
MALFORMED_EVIDENCE + canonical=null + HYDRATABLE
AMBIGUOUS + canonical=null + START_HYDRATION
```

### NO_MATCH proof obligation

`NO_MATCH` is not the generic fallback for `canonical=null`.

It is valid only when:

```text
transport/protocol satisfied
AND semantic payload parseable
AND provider actually answered
AND semantic result is empty
```

## 4. Metamorphic regression vectors

These are designed for lane C implementation tests and lane F behavioral gates.

### Vector A: valid MATCH -> missing entity id

Start from a known-good provider MATCH fixture. Remove only `source_entity_id`.

Expected transition:

```text
VALID_MATCH -> MALFORMED_EVIDENCE
canonical -> null
capability -> not HYDRATABLE
action -> not START_HYDRATION
```

Forbidden:

```text
MALFORMED_EVIDENCE -> SEMANTIC_NO_MATCH
MALFORMED_EVIDENCE -> hash/pending canonical
```

Repeat separately for missing provider id and invalid/missing WGS84.

### Vector B: semantic empty -> timeout

Start from a valid semantic NO_MATCH fixture. Change only the transport behavior to timeout.

Expected:

```text
SEMANTIC_NO_MATCH -> RUNTIME_FAILURE
retryable=false/semantic -> retryable=true/runtime
canonical remains null
```

Forbidden:

`NO_MATCH` remaining unchanged after the transport becomes a timeout.

### Vector C: runtime failure -> provider restored

Same raw destination, same disposable DB:

```text
runtime failure
-> no hydration side effect
-> provider restored
-> valid MATCH
-> canonical created/bound
-> only then may coverage produce HYDRATABLE
```

### Vector D: ambiguous candidate ordering

Reverse the order of the same candidate set.

Expected:

```text
canonical remains null
candidate set semantics unchanged
no silent first-candidate selection
```

## 5. Side-effect firewall

For every state without a trustworthy canonical identity, independently prove:

```text
hydration_operation_created = false
hydration_job_enqueued = false
catalog_mutation_from_untrusted_resolution = false
plan/selectable transition = false
```

Response semantics are insufficient if hidden side effects already advanced the product.

## 6. Audit invariants

ProviderAttempt history must retain the factual distinction that caused the state:

- answered vs not answered;
- endpoint/mirror;
- HTTP/transport result;
- semantic parse status;
- result count where meaningful;
- malformed-contract reason where applicable;
- elapsed time measured around the real transport using a monotonic clock;
- all attempts, not only the final one.

Final product state is derived from this evidence; it must not erase the evidence.

## 7. F gate recommendation

F should gate the matrix as cross-state properties, not mirror implementation predicates.

Minimum black-box assertions through the normal application entry:

```text
HYDRATABLE => canonical != null
START_HYDRATION => HYDRATABLE && canonical != null
NO_MATCH => answered && parseable && semantic_empty
RUNTIME_FAILURE => canonical == null && retryable && !HYDRATABLE
MALFORMED_EVIDENCE => canonical == null && !NO_MATCH && !HYDRATABLE
AMBIGUOUS => canonical == null && !silent_selection && !HYDRATABLE
```

Do not implement the gate by importing and reusing the same product decision function it is meant to judge.

## 8. P7 implication

P7 remains false until the matrix is satisfied on the candidate SHA together with:

- durable/retrievable ProviderAttempt history;
- measured timing;
- malformed-evidence negative witnesses;
- replay/durability/idempotency;
- positive validator calibration and `p7_check.py exit=0`.

> The product state must be a function of provider evidence truth, not merely a function of whether a canonical id happened to be null.