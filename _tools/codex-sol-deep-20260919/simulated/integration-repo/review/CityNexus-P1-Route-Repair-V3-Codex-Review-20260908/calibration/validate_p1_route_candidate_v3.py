"""Final pre-render gate for the P1 UC route candidate.

V3 composes the hardened V2 geometry/contact gate with:
- exact protection of the three C4E1-frozen Extend routes;
- final route-planning status requirements once geometry is clean;
- waypoint coordinate normalization to avoid floating garbage in the frozen YAML.
"""
from __future__ import annotations

import json
import math
import subprocess
import sys
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
RENDERER = HERE.parent
OUT = HERE / "out"
CANDIDATE = RENDERER / "phase1-routing-rc6-candidate.yaml"
V2_REPORT = OUT / "P1_UC_ROUTE_CANDIDATE-v2-report.json"
REPORT = OUT / "P1_UC_ROUTE_CANDIDATE-v3-report.json"

FROZEN_EXTEND = {
    "EXT-07-06": {
        "source": "UC-07",
        "target": "UC-06",
        "sourceSide": "TOP",
        "targetSide": "BOTTOM",
        "sourcePortFraction": 0.5,
        "targetPortFraction": 0.5,
        "waypoints": [[17.2, 6.6], [8.3, 6.6], [8.3, 9.7], [11.1, 9.7]],
    },
    "EXT-09-08": {
        "source": "UC-09",
        "target": "UC-08",
        "sourceSide": "TOP",
        "targetSide": "BOTTOM",
        "sourcePortFraction": 0.5,
        "targetPortFraction": 0.5,
        "waypoints": [[17.2, 10.2], [7.5, 10.2], [7.5, 13.4], [11.1, 13.4]],
    },
    "EXT-10-09": {
        "source": "UC-10",
        "target": "UC-09",
        "sourceSide": "TOP",
        "targetSide": "BOTTOM",
        "sourcePortFraction": 0.5,
        "targetPortFraction": 0.5,
        "waypoints": [[23.3, 9.4], [27.0, 9.4], [27.0, 14.2], [17.2, 14.2]],
    },
}

FINAL_METADATA_STATUS = "GEOMETRY_PASS_PENDING_EXTERNAL_FREEZE"
FINAL_ASSOCIATION_STATUS = "ROUTE_PLANNED_PENDING_EXTERNAL_FREEZE"


def almost_equal(a, b, eps=1e-9):
    return abs(float(a) - float(b)) <= eps


def same_points(actual, expected):
    if not isinstance(actual, list) or len(actual) != len(expected):
        return False
    return all(
        isinstance(a, list)
        and len(a) == 2
        and almost_equal(a[0], e[0])
        and almost_equal(a[1], e[1])
        for a, e in zip(actual, expected)
    )


def normalized_to_2dp(value):
    return almost_equal(float(value), round(float(value), 2))


def main() -> int:
    subprocess.run(
        [sys.executable, str(HERE / "validate_p1_route_candidate_v2.py")],
        check=False,
    )
    v2 = json.loads(V2_REPORT.read_text(encoding="utf-8"))
    candidate = yaml.safe_load(CANDIDATE.read_text(encoding="utf-8"))
    routes = {route["id"]: route for route in candidate["routes"]}

    failures = []

    # Frozen Extend contract.
    for route_id, expected in FROZEN_EXTEND.items():
        route = routes.get(route_id)
        if route is None:
            failures.append(f"missing frozen Extend route:{route_id}")
            continue

        if route.get("connectorType") != "extend":
            failures.append(f"frozen Extend connectorType changed:{route_id}")

        for key in ("source", "target", "sourceSide", "targetSide"):
            if route.get(key) != expected[key]:
                failures.append(f"frozen Extend {key} changed:{route_id}")

        for key in ("sourcePortFraction", "targetPortFraction"):
            if not almost_equal(route.get(key), expected[key]):
                failures.append(f"frozen Extend {key} changed:{route_id}")

        if not same_points(route.get("waypoints"), expected["waypoints"]):
            failures.append(f"frozen Extend waypoints changed:{route_id}")

        if route.get("planningStatus") != "FROZEN_FROM_C4E1":
            failures.append(f"frozen Extend planningStatus changed:{route_id}")

    # No floating garbage in Association waypoint coordinates.
    association_routes = [
        route for route in candidate["routes"]
        if route.get("connectorType") == "association"
    ]
    for route in association_routes:
        for index, point in enumerate(route.get("waypoints") or []):
            if (
                not isinstance(point, list)
                or len(point) != 2
                or not normalized_to_2dp(point[0])
                or not normalized_to_2dp(point[1])
            ):
                failures.append(
                    f"association waypoint not normalized to <=2dp:"
                    f"{route['id']}:{index}:{point!r}"
                )

    # Statuses are only required once the actual geometry/contact gate is clean.
    if v2.get("status") == "PASS":
        if candidate.get("metadata", {}).get("status") != FINAL_METADATA_STATUS:
            failures.append(
                "geometry is PASS but metadata.status is not "
                + FINAL_METADATA_STATUS
            )

        for route in association_routes:
            if route.get("planningStatus") != FINAL_ASSOCIATION_STATUS:
                failures.append(
                    f"geometry is PASS but Association planningStatus is stale:"
                    f"{route['id']}={route.get('planningStatus')!r}"
                )

    payload = {
        "pageName": candidate.get("pageName"),
        "status": "PASS" if v2.get("status") == "PASS" and not failures else "FAIL",
        "v2Status": v2.get("status"),
        "frozenExtendRouteCount": len(FROZEN_EXTEND),
        "associationRouteCount": len(association_routes),
        "metadataStatus": candidate.get("metadata", {}).get("status"),
        "requiredFinalMetadataStatus": FINAL_METADATA_STATUS,
        "requiredFinalAssociationStatus": FINAL_ASSOCIATION_STATUS,
        "failures": failures,
    }

    REPORT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=True, indent=2))
    return 0 if payload["status"] == "PASS" else 1

if __name__ == "__main__":
    raise SystemExit(main())
