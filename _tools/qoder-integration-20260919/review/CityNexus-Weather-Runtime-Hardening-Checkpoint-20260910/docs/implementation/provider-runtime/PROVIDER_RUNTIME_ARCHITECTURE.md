# Provider Runtime Architecture

## Authority chain

```text
Valhalla or deterministic offline provider
        |
        v
validate / normalize provider result
        |
        v
capture_runtime_mobility_snapshot()
        |
        v
operation-scoped immutable MobilitySnapshot
        |
        +--> F3 Opportunity Window
        +--> candidate travel_from_prev_min
        +--> authoritative deterministic feasibility
        +--> verified scoring / ReplanDiff evidence
        |
        v
ReplanProposal.diff_json verified_evidence
        |
        v
JourneyTwin read projection
```

Provider facts are inputs. `evaluate_feasibility()` remains the authority.
Provider, solver and AI outputs cannot activate a PlanVersion or mutate a C4
Commitment by themselves.

## Snapshot scope

The snapshot is scoped to one `Generate Replan` operation. Required OD pairs
are collected before candidate evaluation, normalized and deduplicated, then
captured once. Candidate generation does not make provider calls while it
iterates.

`operation_key` is currently `replan:<trigger_event_id>`. The snapshot also has
a unique `snapshot_id` and a single `captured_at` instant. Every proposal from
the operation persists the same serialized snapshot evidence.

This design makes the candidate set reproducible even if an external provider
would return different values a moment later.

## Provider selection and fallback

Offline/default profile:

```text
MockMobilityProvider -> frozen MobilitySnapshot
```

Opt-in real profile when `CITYNEXUS_LIVE_VALHALLA_URL` is configured:

```text
ValhallaHTTPMobilityProvider
        |
        +-- success for pair --> Valhalla fact
        |
        +-- failure for pair --> MockMobilityProvider fact
                                  degraded=true
                                  fallback_reason recorded
```

Fallback is pair-scoped. A failure for one OD pair does not silently replace
successful Valhalla facts for the rest of the operation.

If neither primary nor fallback can provide a required fact, capture raises
`MobilitySnapshotCaptureError`; the Replan endpoint returns an explicit service
unavailable result instead of inventing an ETA.

## Deterministic gate

The gate accepts deterministic mock facts or an object marked as a frozen
snapshot. A direct live provider is rejected as
`NON_DETERMINISTIC_MOBILITY_PROVIDER` without calling it.

Replan now injects its operation snapshot into `validate_plan_feasibility()`.
The same facts that created candidate travel fields therefore judge their
feasibility.

## JourneyTwin

JourneyTwin is still a projection. On read it looks for the latest persisted
Replan mobility evidence and reconstructs a `MobilitySnapshot`. When the OD
pair required for the next C4 buffer is present, Twin uses that frozen fact.

Twin never calls `capture_runtime_mobility_snapshot()` or Valhalla during a
GET. If no persisted fact covers that pair, the current course-demo fallback
is deterministic mock mobility and is labeled as such in `context.mobility`.

## Why there is no snapshot table in this gate

The current requirement is operation-level immutability, reproducibility and
auditability. Proposal evidence already provides durable storage for all three.
A dedicated table would add schema/migration work without improving the
authoritative decision for the present Golden Scenario. A table becomes useful
later if snapshots need cross-operation reuse, expiry management, independent
querying, or long-lived provider audit retention.
