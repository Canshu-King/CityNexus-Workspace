# P7 Final Closeout Probes

Status at drafting: candidate product SHA `db4a91c`; Commander has independently reproduced live MATCH and live semantic NO_MATCH through the normal capability entry, but P7 remains false.

This document does not add a new gate. It turns the remaining P7 gaps into the shortest deterministic probe set.

## 1. Already reproduced on `db4a91c`

Through `GET /api/v1/destinations/capability` with `CITYNEXUS_ANYWHERE_RESOLVER=photon` on a disposable DB:

- previously-unseeded Gongshan -> provider canonical `OSM:R:2729765` -> `HYDRATABLE` / `START_HYDRATION`;
- provenance includes provider/source id, WGS84 centroid, extent, observed_at;
- synthetic nonexistent county -> `provider_no_match`, `canonical=null`, exact raw preserved, normalized value separate;
- no fallback `unresolved:<hash>` on these normal-path cases.

Treat these as reproduced behavior witnesses, not as proof of full P7.

## 2. Remaining probes, in order

### A. MATCH audit completion

Run the already-working Gongshan MATCH again through the normal entry.

Required witness:

```text
normal request id / operation id
final outcome = MATCH
canonical id
source_provider
source_entity_id
WGS84
full ProviderAttempt history
durable attempt-store location
retrieval command
```

Success-path ProviderAttempt history must exist even though the public capability JSON does not have to expose it.

For a LIVE network call, `elapsed_ms` must be measured by a monotonic clock around the real transport call and be > 0. A fixture/replay may legitimately report zero only when explicitly labeled non-LIVE.

### B. AMBIGUOUS behavior

Do not waste the night hunting a naturally ambiguous Photon query.

Use a deterministic provider/transport fixture that returns two plausible typed candidates, but invoke it through the same normal HTTP/application entry used in production.

Required:

```text
provider_outcome = AMBIGUOUS
canonical_destination_id = null
candidate_count >= 2
candidate source ids preserved
silent_selection = false
raw preserved
normalized preserved
ProviderAttempt history retrievable
evidence_mode = FIXTURE or REPLAY
```

Directly calling the resolver/product function is not sufficient. The application path must consume the typed result.

### C. RUNTIME_FAILURE behavior

Inject one deterministic runtime failure at the provider transport seam, again through the normal HTTP/application entry.

Prefer a timeout or 503 fixture. Required:

```text
provider_outcome = RUNTIME_FAILURE
canonical_destination_id = null
retryable/runtime reason named
collapsed_to_no_match = false
raw preserved
ProviderAttempt records the failure
evidence_mode = FIXTURE or REPLAY
```

Do not use a real outage as the only witness; deterministic reproduction matters more here.

### D. Malformed MATCH rejection

Inject a typed MATCH whose required identity evidence is malformed, one mutation at a time:

1. missing source_provider;
2. missing source_entity_id;
3. invalid/missing WGS84.

Each case must traverse the normal application path and produce a named malformed/invalid-provider-evidence state.

Hard negative:

`canonical_destination_id` must not be synthesized from raw text, pending key, or hash.

### E. Replay / durability / idempotency

Use the same disposable DB and a known MATCH case.

1. issue the normal request;
2. record canonical identity and durable operation/audit key;
3. retrieve full ProviderAttempt history;
4. close and reopen the DB session or restart the test process;
5. replay the same request;
6. retrieve by the same durable association model;
7. verify the canonical identity is stable and no pseudo-canonical/duplicate identity is created;
8. verify the original attempt history remains retrievable.

This closes P7 condition 6.

## 3. Evidence modes

Use the strongest appropriate evidence, but do not confuse categories:

```text
LIVE      = real provider transport
REPLAY    = recorded provider response replayed
FIXTURE   = deterministic injected provider/transport behavior
SYNTHETIC = generated non-provider fact
UNKNOWN   = evidence mode not established
```

P7 behavioral integration does not require every negative branch to be provoked against the live internet. It requires the typed outcome to traverse the real application path without semantic collapse.

## 4. Final P7 positive receipt

Once A-E are complete, generate one receipt tied to:

```text
product_sha = db4a91c (or the exact successor SHA containing the fixes)
validator_sha
receipt_schema_version
receipt_sha256
normal_application_entrypoint
```

Then run `p7_check.py`.

Only `exit=0` plus Commander's independent replay permits:

`P7_RESOLVER_INTEGRATED=true`

After that, follow the frozen wake sequence:

1. rebuild/restart canary on the exact P7 SHA;
2. issue fresh canary identity receipt;
3. Commander smoke;
4. wake Harness + P1/P2/P3/P4;
5. B runs the Gongshan/Yunhe evidence chain.

## 5. Keep separate

Even if P7 closes, the old lane-B `:8596` runtime claim remains `RUNTIME_UNOBSERVED` until its own canary is restarted and its 14-item candidate used-edge receipt is independently reproduced.
