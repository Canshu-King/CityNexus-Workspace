# ORD-0192 Reproduction Protocol

Purpose: convert the current Gongshan/Yunhe E2E report from SELF_REPORTED to REPRODUCED without allowing green tests, aggregate mobility counts, or a stale worktree to substitute for candidate evidence.

## 1. Required handoff from lane B

Commander must receive all of:

- exact commit SHA
- exact worktree path used by lane B
- exact receipt path
- exact command(s) used to run the Gongshan and Yunhe cases
- canary code SHA/build id if a canary runtime was involved
- canary DB identity/copy id if a canary DB was involved

If the SHA is not present in the authoritative repository, status remains SELF_REPORTED.

## 2. Reproduce from immutable bytes

Commander must:

1. create/read a clean `git archive <SHA>`;
2. do not reuse lane B's dirty worktree as evidence;
3. point the run only at a disposable/canary DB;
4. record runtime/provider configuration without exposing secrets;
5. run the same case from the same declared entry path.

A pass from a different tree or an uncommitted worktree is not reproduction.

## 3. Gongshan acceptance receipt

The receipt must include at least:

```text
case
stage
input
preseed_identity_present
preseed_catalog_present
provider_outcome
provider_attempts
canonical_destination_id
source_provider
source_entity_id
wgs84_or_extent
observations_retained
catalog_source_identity_retained
discovery_area_basis
warm_read_gate_used
candidate_id
used_edge_count
used_edge_ids
per_edge_source_kind
per_edge_provider_or_fixture
per_edge_fact_quality
per_edge_hard_eligible
hard_eligible_count
frozen_fixture_count
synthetic_default_count
unknown_count
first_blocking_edge_or_edges
blocker_basis
aggregate_repository_counts_used_as_blocker
final_product_state
blocker_reason
selectable_emitted
evidence_mode
```

Hard acceptance for the reported milestone:

- no preseeded identity/catalog for the proof case;
- real provider evidence is traceable;
- observations are retained;
- provider/source identity survives normalization;
- extent/bbox is used when available instead of an arbitrary fixed 5 km circle;
- warm path proves an actual read gate;
- actual candidate `used_edge_ids` are inventoried;
- at least one actual used edge is not hard-eligible;
- `blocker_basis = USED_EDGE_INVENTORY`;
- `aggregate_repository_counts_used_as_blocker = false`;
- final state is `MOBILITY_EVIDENCE_NOT_HARD_ELIGIBLE` or the exact typed equivalent;
- `selectable_emitted = false`.

If every actual used edge is hard-eligible, this blocker is invalid and the flow must continue to normal SELECTABLE evaluation.

## 4. Evidence mode labeling

Every receipt must say whether each critical stage is:

- LIVE
- REPLAY
- FIXTURE
- SYNTHETIC
- UNKNOWN

"6 live provider rows" is not sufficient by itself. Each live row must identify provider/source identity and the observation/provenance that made it live.

A replayed provider fixture may prove classification behavior, but it does not prove a live provider call.

## 5. Product-level limitation while P7 is false

Even if Gongshan ORD-0192 is reproduced, it MUST NOT be used to set:

`P7_RESOLVER_INTEGRATED=true`

unless the exact reproduced SHA also contains the C product integration that consumes B's typed `ProviderResolution` through the normal application path and satisfies the seven P7 conditions.

Therefore two statuses may coexist:

```text
ORD-0192_GONGSHAN = REPRODUCED
P7_RESOLVER_INTEGRATED = false
```

That is not contradictory. It means the E2E evidence runner reached a truthful blocker, while the authoritative product path still has a resolver-integration gap.

## 6. Yunhe second case

For Yunhe, preserve the first real divergence exactly.

If Photon returns a valid semantic zero and a configured Nominatim fallback is attempted:

- retain both provider attempts;
- do not rewrite the Photon semantic zero as an outage;
- do not declare final NO_MATCH until the configured provider cascade is complete;
- if fallback is unavailable/runtime-failing, classify that separately from semantic zero;
- if fallback resolves, continue the chain;
- if fallback returns semantic zero under a valid transport contract, final NO_MATCH may be valid.

The receipt must make clear whether the blocker is:

- provider semantic no-match,
- provider access/runtime failure,
- fallback policy/configuration,
- canonical/product integration,
- hydration/catalog,
- planner/mobility evidence.

## 7. Commander upgrade rule

Upgrade SELF_REPORTED -> REPRODUCED only after Commander independently reruns the exact SHA/receipt path and verifies the candidate-level receipt.

Do not upgrade based on:

- lane B's summary text;
- a green test count alone;
- repository-wide mobility statistics;
- screenshots without code/DB identity;
- an uncommitted worktree;
- an API-only success that bypasses the declared product/application path.