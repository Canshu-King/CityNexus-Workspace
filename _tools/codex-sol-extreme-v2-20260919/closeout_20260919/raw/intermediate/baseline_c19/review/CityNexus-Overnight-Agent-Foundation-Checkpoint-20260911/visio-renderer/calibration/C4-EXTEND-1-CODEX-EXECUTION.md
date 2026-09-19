# C4 Extend 0.1.1 Codex execution contract

## Frozen state

```text
C1 = FROZEN_PASS
C2 = FROZEN_PASS
C3 = FROZEN_PASS
C4 Association = FROZEN_PASS
Full C4 = EXTEND_REPAIR_PENDING
```

Do not reopen Association routing research and do not modify native connector
Geometry.

## What C4E.1 repairs

The historical C4E output is preserved.

C4E.1 changes only two things:

1. `EXT-07-06` visible route now approaches the declared target BOTTOM side
   vertically from below.
2. RAW SVG text validation parses XML text nodes so numeric entities such as
   `&#60;` and `&#62;` are interpreted correctly.

The validator also adds a mandatory endpoint tangent gate for all three routes.

## Execute

```powershell
cd D:\moodle\CityNexus\visio-renderer

python -m pytest .\tests -q

python .\calibration\build_c4_extend_1.py

python .\calibration\validate_c4_extend_1.py
```

Only if the validator passes:

```powershell
python .\calibration\update_source_input_hashes.py
```

## Required outputs

```text
C4E1_ExtendFallback.vsdx
C4E1_ExtendFallback.raw.svg
C4E1_ExtendFallback.png
C4E1-build-record.json
C4E1_ExtendFallback-report.json
```

## PASS gate

Semantic:

```text
semanticExtendCount = 3
nativeExtendRatio = 1.0
semanticFullyGluedRatio = 1.0
semanticExplicitSidePortRatio = 1.0
semanticDirectionalSidePortRatio = 1.0
semanticHiddenStrokeRatio = 1.0
```

Presentation:

```text
presentationExpectedSegmentCount = presentationActualSegmentCount
presentationSegmentGeometryMatchRatio = 1.0
presentationSegmentStyleRatio = 1.0
presentationExactRouteRatio = 1.0
presentationOrthogonalRouteRatio = 1.0
presentationEndpointTangentRatio = 1.0
terminalOpenArrowRatio = 1.0
```

Text:

```text
extendLabelRatio = 1.0
extendConditionRatio = 1.0
extendTextStyleRatio = 1.0
rawSvgVisibleExtendLabelCount = 3
rawSvgVisibleConditionCount = 3
```

Quality:

```text
connectorConnectorCrossingCount = 0
connectorOverlapPairCount = 0
connectorThroughUnrelatedNodeCount = 0
outOfPageCount = 0
#VALUE! = 0
#REF! = 0
#NAME? = 0
```

## Stop rule

If C4E.1 fails, do not create another routing architecture. Preserve the new
artifacts and report for external review.

If C4E.1 passes, set only:

```text
C4 = EXTEND_CALIBRATION_PASS_PENDING_EXTERNAL_FREEZE
```

Do not render formal P1 or RC6 yet.
