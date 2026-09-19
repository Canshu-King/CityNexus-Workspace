"""Static geometry validator for the C4 calibration routing plan."""
from __future__ import annotations

import json
from pathlib import Path
import sys
import yaml

HERE = Path(__file__).resolve().parent
RENDERER = HERE.parent
sys.path.insert(0, str(RENDERER))
from routing_geometry import (  # noqa: E402
    count_crossings,
    count_overlaps,
    node_box,
    path_is_orthogonal,
    route_points,
    segment_intersects_box_interior,
)

SPEC = HERE / "c4-routing-calibration-spec.yaml"
OUT = HERE / "out" / "C4_Routing_Plan-report.json"


def main() -> int:
    spec = yaml.safe_load(SPEC.read_text(encoding="utf-8"))
    nodes = {x["id"]: x for x in spec["nodes"]}
    routes = {x["id"]: x for x in spec["routes"]}
    failures: list[str] = []
    paths = {}
    records = {}

    for rid, route in routes.items():
        if route["source"] not in nodes or route["target"] not in nodes:
            failures.append(f"dangling endpoint:{rid}")
            continue
        pts = route_points(route, nodes)
        paths[rid] = pts
        orth = path_is_orthogonal(pts)
        through = []
        for nid, node in nodes.items():
            if nid in {route["source"], route["target"]}:
                continue
            b = node_box(node)
            if any(segment_intersects_box_interior(a, c, b) for a, c in zip(pts, pts[1:])):
                through.append(nid)
        if not orth:
            failures.append(f"non-orthogonal:{rid}")
        if through:
            failures.append(f"through-node:{rid}:{','.join(through)}")
        records[rid] = {"points": pts, "orthogonal": orth, "throughNodes": through}

    crossings = count_crossings(paths)
    overlaps = count_overlaps(paths)
    if len(crossings) > int(spec["policy"]["maxConnectorCrossings"]):
        failures.append(f"crossings:{len(crossings)}")
    # The calibration deliberately avoids shared/overlapping route segments too.
    if overlaps:
        failures.append(f"overlapping-routes:{len(overlaps)}")

    payload = {
        "calibration": "C4-PLAN",
        "status": "PASS" if not failures else "FAIL",
        "routeCount": len(routes),
        "orthogonalRouteCount": sum(1 for x in records.values() if x["orthogonal"]),
        "connectorCrossingCount": len(crossings),
        "connectorOverlapPairCount": len(overlaps),
        "crossings": crossings,
        "overlaps": overlaps,
        "records": records,
        "failures": failures,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=True, indent=2))
    return 0 if payload["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
