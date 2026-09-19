from __future__ import annotations
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "out"
REPORT = OUT / "C4_FREEZE-report.json"

ASSOC_ONE = [
    "nativeAssociationRatio","semanticFullyGluedRatio",
    "semanticExplicitSidePortRatio","semanticDirectionalSidePortRatio",
    "semanticHiddenStrokeRatio","presentationSegmentGeometryMatchRatio",
    "presentationSegmentStyleRatio","presentationExactRouteRatio",
    "presentationOrthogonalRouteRatio",
]
EXT_ONE = [
    "nativeExtendRatio","semanticFullyGluedRatio",
    "semanticExplicitSidePortRatio","semanticDirectionalSidePortRatio",
    "semanticHiddenStrokeRatio","presentationSegmentGeometryMatchRatio",
    "presentationSegmentStyleRatio","presentationExactRouteRatio",
    "presentationOrthogonalRouteRatio","presentationEndpointTangentRatio",
    "terminalOpenArrowRatio","extendLabelRatio","extendConditionRatio",
    "extendTextStyleRatio",
]
ZERO = [
    "connectorConnectorCrossingCount","connectorOverlapPairCount",
    "connectorThroughUnrelatedNodeCount","outOfPageCount",
]

def load(name):
    p = OUT / name
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None

def main():
    a = load("C4F_SemanticOverlay-report.json")
    e = load("C4E1_ExtendFallback-report.json")
    failures = []
    if not a: failures.append("missing association report")
    if not e: failures.append("missing extend report")

    if a:
        if a.get("status") != "PASS": failures.append("association status != PASS")
        if a.get("semanticConnectorCount") != 5: failures.append("association count != 5")
        if a.get("presentationExpectedSegmentCount") != a.get("presentationActualSegmentCount"):
            failures.append("association segment-count mismatch")
        for k in ASSOC_ONE:
            if a.get(k) != 1.0: failures.append(f"association:{k}={a.get(k)!r}")
        for k in ZERO:
            if a.get(k) != 0: failures.append(f"association:{k}={a.get(k)!r}")
        for t in ("#VALUE!","#REF!","#NAME?"):
            if a.get("forbiddenTokenCounts",{}).get(t) != 0:
                failures.append(f"association:{t}")

    if e:
        if e.get("status") != "PASS": failures.append("extend status != PASS")
        if e.get("semanticExtendCount") != 3: failures.append("extend count != 3")
        if e.get("presentationExpectedSegmentCount") != e.get("presentationActualSegmentCount"):
            failures.append("extend segment-count mismatch")
        if e.get("rawSvgVisibleExtendLabelCount") != 3:
            failures.append("extend visible-label count != 3")
        if e.get("rawSvgVisibleConditionCount") != 3:
            failures.append("extend visible-condition count != 3")
        for k in EXT_ONE:
            if e.get(k) != 1.0: failures.append(f"extend:{k}={e.get(k)!r}")
        for k in ZERO:
            if e.get(k) != 0: failures.append(f"extend:{k}={e.get(k)!r}")
        for t in ("#VALUE!","#REF!","#NAME?"):
            if e.get("forbiddenTokenCounts",{}).get(t) != 0:
                failures.append(f"extend:{t}")

    payload = {
        "milestone": "C4_FULL",
        "status": "PASS" if not failures else "FAIL",
        "associationCalibration": "C4F",
        "extendCalibration": "C4E1",
        "failures": failures,
    }
    REPORT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=True, indent=2))
    return 0 if not failures else 1

if __name__ == "__main__":
    raise SystemExit(main())
