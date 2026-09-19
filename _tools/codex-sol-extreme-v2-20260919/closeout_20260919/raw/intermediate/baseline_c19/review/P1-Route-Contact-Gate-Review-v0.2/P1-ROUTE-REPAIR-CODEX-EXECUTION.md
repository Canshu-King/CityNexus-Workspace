# P1 route repair execution contract

Frozen renderer baseline:

```text
C1 = FROZEN_PASS
C2 = FROZEN_PASS
C3 = FROZEN_PASS
C4 = FROZEN_PASS
```

Do not reopen C4, Visio Geometry mutation, or routing-tool research.

## Scope

Edit only:

```text
visio-renderer/phase1-routing-rc6-candidate.yaml
```

and, only as needed to install this QA patch:

```text
visio-renderer/calibration/audit_p1_route_contacts.py
visio-renderer/calibration/validate_p1_route_candidate_v2.py
visio-renderer/tests/test_p1_route_contact_gate_contract.py
```

Do not change domain-model, requirements, use-cases, or
`visio-spec/pages/p1_uc_overview.yaml`.

The 3 frozen Extend routes must remain unchanged unless an external review
explicitly reopens them.

## Why repair is required

The old validator reports 0 proper crossings and 0 overlaps, but independent
geometry inspection found:

```text
contactPairCount = 46
uniqueContactCount = 55

tjunction = 22
shared_endpoint = 33
```

These contacts were not part of the historical gate.

## Workflow

Run:

```powershell
cd D:\moodle\CityNexus\visio-renderer

python -m pytest .\tests -q

python .\calibration\validate_p1_route_candidate_v2.py
```

The first v2 run is EXPECTED TO FAIL.

Use:

```text
calibration/out/P1_UC_ROUTE_CONTACT-AUDIT.json
```

as the exact repair list.

Reroute only the 18 Association relations.

## Required final gate

The route plan is acceptable only when all of the following hold:

```text
historical base gate = PASS

semanticConnectorCount = 21
candidateRouteCount = 21
explicitGeometryRouteCount = 21

properCrossingCount = 0
collinearOverlapPairCount = 0

contactPairCount = 0
uniqueContactCount = 0

tjunction = 0
shared_endpoint = 0

shortSegmentCount = 0
redundantCollinearPointCount = 0
```

All historical requirements still apply:

```text
orthogonal
endpoint tangency correct
no unrelated-node traversal
inside page bounds
```

Prefer simple routes with few bends. Do not create 0.02-0.05 cm micro-jogs.

## State update after PASS

Only after v2 PASS:

```text
metadata.status = GEOMETRY_PASS_PENDING_EXTERNAL_FREEZE
```

For the 18 Association routes:

```text
planningStatus = ROUTE_PLANNED_PENDING_EXTERNAL_FREEZE
```

Keep the 3 Extend routes:

```text
planningStatus = FROZEN_FROM_C4E1
```

## Stop

When `validate_p1_route_candidate_v2.py` first returns PASS:

- do not render Visio;
- do not generate RC6;
- package the candidate YAML, both route reports, the contact audit, and the
  validator source for GPT external review;
- STOP.
