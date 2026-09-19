# C4 Extend calibration Codex execution contract

## Frozen state

- C1 = FROZEN_PASS
- C2 = FROZEN_PASS
- C3 = FROZEN_PASS
- C4 Association fallback = FROZEN_PASS
- full C4 = EXTEND_CALIBRATION_PENDING

Do not reopen native Association Geometry experiments. Do not create C4.1e.

## Purpose

Calibrate only the three formal Phase 1 `<<extend>>` relations:

```text
EXT-07-06  UC-07 -> UC-06  [payment required]
EXT-09-08  UC-09 -> UC-08  [event detected]
EXT-10-09  UC-10 -> UC-09  [replan required]
```

The semantic layer must use the genuine Microsoft UML `Extend` master.

The presentation layer must use deterministic dashed route segments, with one
terminal open arrow pointing to the target/base use case, plus explicit
`<<extend>>` and condition labels.

## Required execution

```powershell
cd D:\moodle\CityNexus\visio-renderer

python -m pytest .\tests -q

python .\calibration\build_c4_extend.py

python .\calibration\validate_c4_extend.py
```

## Required outputs

```text
C4E_ExtendFallback.vsdx
C4E_ExtendFallback.raw.svg
C4E_ExtendFallback.png
C4E-build-record.json
C4E_ExtendFallback-report.json
```

## PASS gate

Semantic layer:

```text
semanticExtendCount = 3
nativeExtendRatio = 1.0
semanticFullyGluedRatio = 1.0
semanticExplicitSidePortRatio = 1.0
semanticDirectionalSidePortRatio = 1.0
semanticHiddenStrokeRatio = 1.0
```

Presentation layer:

```text
presentationExpectedSegmentCount = presentationActualSegmentCount
presentationSegmentGeometryMatchRatio = 1.0
presentationSegmentStyleRatio = 1.0
presentationExactRouteRatio = 1.0
presentationOrthogonalRouteRatio = 1.0
terminalOpenArrowRatio = 1.0
extendLabelRatio = 1.0
extendConditionRatio = 1.0
extendTextStyleRatio = 1.0

connectorConnectorCrossingCount = 0
connectorOverlapPairCount = 0
connectorThroughUnrelatedNodeCount = 0
outOfPageCount = 0
```

No `#VALUE!`, `#REF!`, or `#NAME?`.

## Stop rule

If C4E fails, do not generate RC6 and do not change the routing architecture.
Return the C4E artifacts/report for external review.

If C4E passes, set:

```text
C4 = EXTEND_CALIBRATION_PASS_PENDING_EXTERNAL_FREEZE
```

and stop. Do not render the formal P1 page or RC6 yet.
