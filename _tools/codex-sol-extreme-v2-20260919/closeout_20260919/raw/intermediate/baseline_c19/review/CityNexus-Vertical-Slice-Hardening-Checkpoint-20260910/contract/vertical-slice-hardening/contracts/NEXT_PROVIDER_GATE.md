# Next Bounded Gate - Sourced/Frozen Mobility Runtime

**Do not execute this gate until Vertical Slice Hardening receives external freeze.**

This file exists so Codex does not waste another long run rediscovering the provider architecture.

## Objective

Move CityNexus from:

```text
Valhalla adapter exists
+ MobilitySnapshot type exists
+ gate accepts frozen snapshot
+ product runtime still instantiates MockMobilityProvider directly
```

to:

```text
provider call outside authority
-> normalized travel facts
-> one frozen MobilitySnapshot
-> deterministic replan/feasibility/scoring evidence
-> explicit provenance/degradation
```

while retaining a fully deterministic offline demo.

## Authority rule

Never perform live HTTP inside:

- `evaluate_feasibility`
- authoritative scoring
- JourneyTwin projection reads
- accept-time feasibility revalidation

Provider calls occur before authority and are frozen into facts.

## Existing foundation to reuse

Do not rewrite these just to look productive:

```text
app/integrations/mobility/valhalla_http.py
app/integrations/mobility/snapshot_capture.py
app/replanning/provider_snapshots.py
app/replanning/feasibility.py
```

Existing tests already prove:

- live provider objects are rejected inside deterministic feasibility;
- frozen MobilitySnapshot is accepted;
- per-pair primary/fallback provenance is retained;
- Valhalla HTTP parser can be tested with `httpx.MockTransport` without network.

## Current runtime seams that still need replacement

At review time, direct `MockMobilityProvider()` use still exists in important runtime paths, including:

- plan-selection feasibility
- JourneyTwin next-C4 travel/buffer calculation
- replan generation/F3 travel calculations
- proposal verified mobility evidence, which reports hardcoded `mock-mobility`

Do not change all of these by global search/replace. Decide which command owns a frozen snapshot and thread that fact through deliberately.

## Recommended bounded design

### 1. Create a runtime snapshot service

Introduce a small application-layer seam, for example conceptually:

```python
capture_journey_mobility_snapshot(journey, activities, candidate_places, ...)
```

It should:

- collect the exact origin/destination pairs needed for one planning/replan operation;
- select primary provider from explicit config/dependency;
- use Mock provider as explicit fallback when demo/offline mode requires it;
- call `capture_mobility_snapshot` outside the gate;
- return one immutable snapshot plus capture/degradation metadata.

Do not make the deterministic gate know how to construct Valhalla.

### 2. Pair discovery must be complete before evaluation

For a replan operation collect all needed pairs before freezing, including as applicable:

- current execution origin -> replacement candidate
- replacement candidate -> next C4
- consecutive activities used by feasibility
- old-plan pairs needed to calculate a comparable travel delta
- new-plan candidate pairs needed by scoring/diff

A missing pair must be an explicit controlled failure or explicit fallback capture. Never silently invent zero travel.

### 3. One operation, one evidence snapshot

Within one proposal-generation operation, use the same frozen travel facts for:

- F3 inbound/outbound
- candidate schedule construction
- authoritative feasibility
- travel delta
- verified score inputs
- `verified_evidence.mobility`

Do not ask provider again halfway through and create two realities for one proposal.

### 4. Provenance is per fact

`MobilitySnapshot` already retains `TravelEstimateFact.provider_key` and `degraded`.

Proposal evidence should expose at least:

```text
snapshot source
captured_at
whether degraded
providers actually used
fallback pair count or relevant pair provenance
```

Do not write `provider: valhalla` if one critical pair came from fallback Mock.

### 5. Offline-first remains mandatory

Default coursework/demo path:

```text
no live network required
```

A sensible policy:

```text
live URL absent
-> primary deterministic Mock capture
-> frozen snapshot
-> provider mode clearly marked DEMO/OFFLINE

live URL configured
-> Valhalla primary
-> deterministic Mock fallback only if policy allows
-> frozen snapshot marked degraded when fallback used
```

The exact provider factory may differ, but the evidence must never pretend Mock is Valhalla.

### 6. JourneyTwin must remain a read projection

Do not turn GET `/twin` into a hidden network operation.

If Twin needs travel evidence, project from already captured/persisted planning/runtime evidence or an operation-owned snapshot reference. A GET request should not change domain truth because Valhalla happened to answer differently five seconds later.

## Required tests for next gate

Write tests before broad implementation. They must use fake providers or `httpx.MockTransport`, not live internet.

### PRT-01 same-snapshot authority

A fake provider returns one set of minutes on first call and different minutes on subsequent calls. Generate one replan. Assert provider capture occurs only at the outer capture boundary and the proposal's F3, gate, travel delta, score evidence all reflect the frozen first set rather than later values.

### PRT-02 primary provenance

Valhalla-like fake succeeds for every pair. Proposal verified evidence reports non-degraded sourced snapshot and no fallback facts.

### PRT-03 partial fallback provenance

Primary fails one pair; Mock fallback fills exactly that pair. Proposal remains deterministic, snapshot is degraded, and evidence identifies fallback usage.

### PRT-04 no safe fact

Primary and fallback fail a required pair. Replan must fail controllably or omit the affected candidate with a machine-readable reason. Never assume zero minutes.

### PRT-05 no network inside gate

Keep existing non-deterministic-provider rejection and add a spy proving `evaluate_feasibility` consumes only the snapshot object.

### PRT-06 Twin read does not call live provider

Repeated GET Twin must not invoke Valhalla/live adapter.

### PRT-07 offline Golden Scenario

No live URL, no internet. Full Golden Scenario remains green through frozen Mock facts.

### PRT-08 optional Valhalla contract

Use `httpx.MockTransport` to emulate Valhalla route/matrix responses and prove runtime capture wiring without external network.

## Stop condition

Stop for review when:

- all previous vertical-slice tests remain green;
- new provider-runtime tests are green;
- offline Golden Scenario still works;
- no live HTTP occurs inside deterministic authority/read projections;
- proposal evidence accurately reflects snapshot provenance;
- live Valhalla remains optional.

Do not combine this gate with OR-Tools or AI integration. Solver/provider/AI arriving in one giant patch is how debugging becomes archaeology.
