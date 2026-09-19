# T2 — Real Replan Path Gate

## Why the current patch is insufficient

The current real flow creates `mobility_pairs` for:
- existing source adjacencies;
- replacement-choice inbound/outbound legs;
- v2 candidate combinations.

It then captures those pairs with the default non-strict runtime mobility
capture.

That can materialize `default_minutes=20` before `_replan_estimate()` runs.

## Required design

Choose a design that guarantees fact quality at the point hard feasibility
consumes it.

Recommended shape:

### 1. Distinguish fact quality

A replan fact must be classified as one of:
- LIVE_MEASURED / LIVE_CAPTURE
- SEALED_REPLAY with acceptable provenance
- EXPLICIT_FROZEN_FIXTURE (demo/test only)
- SYNTHETIC_DEFAULT
- UNAVAILABLE

`SYNTHETIC_DEFAULT` is never hard-feasibility eligible.

For a real Xiaomi trial, synthetic fixture facts should not masquerade as live
routing truth.

### 2. Candidate-specific missing data

Do not abort every replacement just because one candidate has an unavailable
leg.

For each candidate:
- resolve every required adjacency;
- if one required leg is unavailable, mark that candidate unavailable;
- continue other candidates;
- if at least one candidate has complete trustworthy mobility, it may proceed;
- if all otherwise-eligible candidates lack mobility, return
  `MOBILITY_DATA_UNAVAILABLE`.

### 3. Previously frozen facts

A frozen fact is not automatically trustworthy merely because it exists.

Reject or downgrade a previously frozen fact if its provenance shows it came
from the blanket synthetic default.

### 4. Initialize state before first possible use

Move mobility-unavailable tracking before any heuristic/spec construction that
may call `_replan_estimate()`.

Do not leave a latent `UnboundLocalError` path.

## Required endpoint regressions

These must call the actual replan endpoint or the full generate_replan service
path.

1. Missing candidate pair, no live provider:
   - never stores/uses 20 as hard truth;
   - returns `MOBILITY_DATA_UNAVAILABLE` when all candidates need unavailable
     legs.

2. Two candidates:
   - candidate A has trustworthy mobility;
   - candidate B is unavailable;
   - A can still proceed.

3. Previously frozen blanket-default fact:
   - must not be accepted as hard truth.

4. Explicit known fact:
   - remains usable.

5. Genuine overlap / travel-gap violation with trustworthy facts:
   - still rejected by the deterministic gate.

6. Evidence:
   - proposal/snapshot contains no hard-fact entry sourced from synthetic
     default 20.

## UI

Mapped known reasons -> traveler copy.

Unknown internal reason -> generic safe traveler copy.

Raw reason -> Advanced only.
