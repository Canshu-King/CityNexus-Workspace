# T2 hard truth gate

## 1. Use the allowlist

`hard_minutes()` should accept only fact qualities explicitly eligible for hard
feasibility.

Expected shape:

- EXPLICIT_FROZEN_FIXTURE -> allowed for deterministic test/demo facts
- LIVE_PROVIDER_CAPTURE -> allowed
- SYNTHETIC_DEFAULT -> rejected
- LEGACY_UNKNOWN / None -> rejected for hard feasibility
- unknown future string -> rejected

Do not define an allowlist and then use a denylist.

## 2. Legacy snapshots

A pre-v2 snapshot may contain a 20-minute mock fallback with no provenance tag.

Therefore `None` cannot be assumed trustworthy.

Options:
- re-capture when possible;
- migrate only facts whose provenance can actually be established;
- otherwise fail closed.

Regression:
an untagged 20-minute fact must NOT be accepted by `hard_minutes()`.

## 3. Fact-quality classification must fail closed

If a provider exposes a fact-quality method and classification fails:
do not silently infer "explicit/live" from a broad provider-key heuristic.

Prefer explicit trusted provider classification.

Unknown provider provenance -> unavailable for hard truth.

## 4. Candidate-specific endpoint proof

Create a deterministic endpoint/service scenario:

- candidate A has all trustworthy required legs;
- candidate B has at least one unavailable/synthetic leg;
- no unrelated constraint makes A invalid.

Required:
- endpoint returns 201;
- proposal identifies A;
- B is not accepted as hard-feasible;
- no synthetic/default fact enters the hard evidence.

The current test accepting 422 is insufficient.

## 5. Endpoint all-unavailable proof

Keep the useful current proof:
all candidate legs unavailable -> 422 MOBILITY_DATA_UNAVAILABLE.

Also assert stored/evidence facts do not contain a synthetic default consumed by
hard feasibility.
