"""Prepare a Traveler-corridor reference plan without touching the candidate.

The Traveler skeleton is an explicit input.  No hidden handoff-directory path
is allowed, so review packages remain reproducible on another machine.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

import yaml
import networkx as nx

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
sys.path.insert(0, str(HERE.parent))

from routing_geometry import route_points, path_is_orthogonal, node_box, segment_intersects_box_interior
from audit_p1_route_contacts import classify_contact, collinear_redundant
from validate_p1_route_candidate import tangent_ok


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--traveler-skeleton", type=Path, required=True)
    args = parser.parse_args()

    sem = yaml.safe_load((ROOT / "visio-spec/pages/p1_uc_overview.yaml").read_text(encoding="utf-8"))
    cand = yaml.safe_load((HERE.parent / "phase1-routing-rc6-candidate.yaml").read_text(encoding="utf-8"))
    sk = yaml.safe_load(args.traveler_skeleton.read_text(encoding="utf-8"))
    nodes = {n["id"]: n for n in sem["shapes"] if n["id"] != "BOUNDARY"}

    for route in sk["routes"]:
        for end, point in (("source", route["waypoints"][0]), ("target", route["waypoints"][-1])):
            box = node_box(nodes[route[end]])
            side = route[end + "Side"]
            route[end + "PortFraction"] = (
                (point[1] - box.top) / (box.bottom - box.top)
                if side in ("LEFT", "RIGHT")
                else (point[0] - box.left) / (box.right - box.left)
            )

    routes = sk["routes"] + [r for r in cand["routes"] if r["connectorType"] == "extend"]
    paths = {r["id"]: route_points(r, nodes) for r in routes}
    failures = []
    for route in routes:
        points = paths[route["id"]]
        if not path_is_orthogonal(points) or not tangent_ok(points, route["sourceSide"], route["targetSide"]):
            failures.append([route["id"], "orthogonality/tangency"])
            continue
        for a, b in zip(points, points[1:]):
            if abs(a[0] - b[0]) + abs(a[1] - b[1]) < 0.1 - 1e-8:
                failures.append([route["id"], "short segment"])
            for nid, node in nodes.items():
                if nid not in (route["source"], route["target"]) and segment_intersects_box_interior(a, b, node_box(node)):
                    failures.append([route["id"], "node", nid])
        if any(collinear_redundant(*points[i:i + 3]) for i in range(len(points) - 2)):
            failures.append([route["id"], "redundancy"])

    contacts = []
    for i, ra in enumerate(routes):
        for rb in routes[i + 1:]:
            if any(
                classify_contact(a, b, c, d)
                for a, b in zip(paths[ra["id"]], paths[ra["id"]][1:])
                for c, d in zip(paths[rb["id"]], paths[rb["id"]][1:])
            ):
                contacts.append([ra["id"], rb["id"]])

    graph = nx.Graph((c["source"], c["target"]) for c in sem["connectors"])
    plan = []
    for route in cand["routes"]:
        if route["connectorType"] != "association":
            continue
        ref = next((x for x in sk["routes"] if x["id"] == route["id"]), route)
        batch = "A"
        if route["id"] in ("A-CD-UC-10", "A-M-UC-10", "A-T-UC-10", "A-T-UC-11"):
            batch = "B"
        elif route["id"] in ("A-B-06", "A-PA-07"):
            batch = "C"
        elif route["id"] in ("A-M-UC-08", "A-CE-09", "A-M-UC-04"):
            batch = "D"
        elif route["id"] in ("A-CD-UC-04", "A-CD-UC-05"):
            batch = "E"
        plan.append({
            "id": route["id"], "batch": batch,
            "sourceSide": ref["sourceSide"], "sourcePortFraction": ref["sourcePortFraction"],
            "targetSide": ref["targetSide"], "targetPortFraction": ref["targetPortFraction"],
            "referenceWaypoints": ref["waypoints"],
            "status": "PROVISIONAL_NOT_GLOBALLY_VALIDATED",
        })

    out = HERE / "out"; out.mkdir(exist_ok=True)
    (out / "P1-CORRIDOR-PREPLAN.json").write_text(json.dumps(plan, indent=2), encoding="utf-8")
    (out / "P1-TRAVELER-EXACT-REFERENCE.yaml").write_text(yaml.safe_dump(sk, sort_keys=False), encoding="utf-8")
    report = {
        "abstractGraphPlanar": nx.check_planarity(graph)[0],
        "subgraphRouteCount": len(routes),
        "failures": failures,
        "contactPairs": contacts,
        "globalGeometrySolved": False,
        "travelerSkeleton": str(args.traveler_skeleton),
    }
    (out / "P1-PREPLAN-VALIDATION.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if not failures and not contacts else 2


if __name__ == "__main__":
    raise SystemExit(main())
