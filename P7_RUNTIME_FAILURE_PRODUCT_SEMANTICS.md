# P7 Runtime Failure Product-Semantics Gate

Purpose: close the newly reproduced case where provider resolution correctly returns a runtime failure but the product still advertises `HYDRATABLE / START_HYDRATION`.

This is a P7 behavioral-semantic blocker, not merely a UI wording issue.

## 1. Frozen invariant

If destination resolution has not produced a trustworthy canonical identity because the provider did not answer, the product must not invite hydration.

Required invariant:

```text
provider_outcome = RUNTIME_FAILURE
canonical_destination_id = null
=> capability != HYDRATABLE
=> recommended_action != START_HYDRATION
=> no hydration operation is created
=> state remains explicitly retryable / resolver-unavailable
```

Do not invent a new public enum solely for this test if an existing retryable/unavailable state already expresses the semantics. The invariant matters more than the label.

## 2. Two mandatory runtime-failure witnesses

Run both through the normal application entry on the same product SHA:

### Provider unreachable

Expected provider/audit classification:

`PROVIDER_UNREACHABLE`

Expected product semantics:

- `canonical_destination_id = null`
- `retryable = true`
- capability is not HYDRATABLE
- action is a retry/resolution action, not hydration
- no hydration operation/job is created

### Provider timeout

Expected provider/audit classification:

`PROVIDER_TIMEOUT`

Expected product semantics are the same as above.

The two provider failures may share the same public product reason if desired, but the audit layer must retain their distinct causes.

## 3. Transition witness

After one runtime-failure case, restore a working provider and replay the same raw destination.

Required:

- retry path can resolve to MATCH;
- server-owned canonical identity is then created/bound;
- only after identity is trustworthy may the product transition to HYDRATABLE;
- the earlier runtime-failure audit history remains retrievable;
- no pseudo-canonical identity was created during the failed attempt.

This proves the retryable state is a temporary truth state rather than a dead end.

## 4. Hydration side-effect firewall

On a runtime-failure response, independently inspect the disposable DB / operation store and prove:

```text
hydration_operation_created = false
hydration_job_enqueued = false
catalog_mutation_from_failed_resolution = false
```

A response label alone is insufficient if a hidden hydration job was already scheduled.

## 5. Timing audit

For live/provider transport attempts, measure elapsed time around the real transport operation using a monotonic clock.

Acceptance:

- forced timeout must record a non-zero elapsed duration consistent with the configured timeout;
- connection-refused may be very small, but must be measured rather than hard-coded;
- `elapsed_ms = 0.0` for both refusal and a real timeout is evidence that timing is not wired.

Timing quality is an audit defect, but the runtime-failure capability/action bug is the P7 semantic blocker.

## 6. P7 status implication

The following can simultaneously be true:

```text
P7 condition 5 (unresolved outcomes keep canonical=null) = PASS
RUNTIME_FAILURE typed classification = REPRODUCED
RUNTIME_FAILURE product semantics = FAIL/PARTIAL
P7_RESOLVER_INTEGRATED = false
```

Therefore do not describe P7 as 'only malformed + idempotency remaining' until this product-state/action defect and durable ProviderAttempt retrieval are also closed.

## 7. Minimal regression gate

At minimum add a normal-entry regression test equivalent to:

```text
given provider answered=false / runtime failure
when capability is requested
then canonical is null
and capability is not HYDRATABLE
and action is not START_HYDRATION
and no hydration side effect exists
and retryable resolver-unavailable semantics are preserved
```

Repeat once for unreachable and once for timeout.