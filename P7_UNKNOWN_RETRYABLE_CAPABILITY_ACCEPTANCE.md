# P7 UNKNOWN_RETRYABLE Capability Acceptance

Purpose: freeze the fourth Anywhere capability state selected by arbitration and prevent temporary resolver failure from being misrepresented as either HYDRATABLE or structural UNAVAILABLE.

## 1. Frozen capability vocabulary

```text
READY
HYDRATABLE
UNAVAILABLE
UNKNOWN_RETRYABLE
```

`UNKNOWN_RETRYABLE` is the selected fourth state.

## 2. When UNKNOWN_RETRYABLE applies

Use `UNKNOWN_RETRYABLE` only when all of the following hold:

```text
destination resolution was attempted
no trustworthy canonical identity was established
the resolver/provider outcome is runtime/transient
retryable = true
```

Examples:

- connection refused;
- timeout;
- DNS/transport failure;
- provider 429/5xx where retry semantics apply;
- other explicitly transient resolver-unavailable outcomes.

## 3. What it must NOT absorb

`UNKNOWN_RETRYABLE` must not become another generic null-canonical bucket.

Keep these distinct:

```text
AMBIGUOUS               -> ambiguity/disambiguation product state
SEMANTIC_NO_MATCH        -> UNAVAILABLE / refine-or-change-destination semantics
MALFORMED_EVIDENCE       -> named provider evidence/contract failure, retryable as defined by policy
VALID_MATCH + incomplete coverage -> HYDRATABLE
VALID_MATCH + sufficient coverage -> READY
```

Malformed provider evidence must not be mislabeled as `PROVIDER_NO_RESULTS` merely because canonical identity is null.

## 4. Product semantics

For `UNKNOWN_RETRYABLE`:

```text
canonical_destination_id = null
retryable = true
capability = UNKNOWN_RETRYABLE
recommended_action = retry destination resolution / retry later
recommended_action != START_HYDRATION
hydration_operation_created = false
hydration_job_enqueued = false
catalog_mutation_from_failed_resolution = false
```

Human copy should communicate temporary uncertainty, not structural impossibility.

## 5. Atomic contract migration

The state must be added coherently across:

- backend frozen enum/vocabulary;
- `contracts/openapi-anywhere-draft.yaml`;
- frontend/client type or decoder;
- UI state mapping and recovery action;
- tests/gates;
- any telemetry schema that enumerates capability values.

Do not merge a backend-only enum addition that older product code cannot render correctly.

## 6. R14 attribution fields

R14 requires the following four keys to exist in the canonical attribution object:

```text
attribution_reason
evidence_kind
http_status
source_layer
```

Important: key presence is mandatory; universal non-nullness is NOT.

`http_status` must remain null when no HTTP response existed, for example DNS failure, timeout, or connection refusal.

Forbidden:

- inventing `0`, `599`, or another fake HTTP status merely to satisfy a non-empty gate;
- silently defaulting a missing attribution key;
- letting each consumer reconstruct its own classification.

For cases without an HTTP response, `attribution_reason`, `evidence_kind`, and `source_layer` must explain the evidence source and failure mode while `http_status = null` remains truthful.

## 7. F gates

Minimum black-box gates through the normal application path:

```text
runtime failure + no canonical -> capability == UNKNOWN_RETRYABLE
UNKNOWN_RETRYABLE -> retryable == true
UNKNOWN_RETRYABLE -> action != START_HYDRATION
UNKNOWN_RETRYABLE -> no hydration side effects
semantic no-match -> capability != UNKNOWN_RETRYABLE
malformed evidence -> reason != PROVIDER_NO_RESULTS
timeout/refused -> http_status key exists and value may be null
delete any R14 key -> RED
replace missing key with silent default -> RED
```

## 8. P7 relationship

Adding the fourth state does not by itself complete P7.

P7 still requires:

- correct malformed-evidence attribution;
- complete success-path ProviderAttempt history;
- measured attempt timing;
- durable/retrievable audit history;
- replay/idempotency including no duplicate canonical identity;
- positive `p7_check.py` result on the exact product SHA.

> UNKNOWN_RETRYABLE means 'capability cannot yet be truthfully determined because resolution failed transiently'; it does not mean HYDRATABLE, and it does not mean the destination is structurally unavailable.