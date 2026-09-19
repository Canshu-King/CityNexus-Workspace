"""Independent connector-contact audit for the formal P1 use-case route plan.

The historical gate counted only interior H/V crossings and collinear overlaps.
That misses two visually ambiguous cases:

1. a bend/segment endpoint touching the interior of another connector (T-junction);
2. two unrelated connectors sharing an intermediate waypoint.

This script treats every cross-route contact as a defect.  It does not use Visio
or COM and is suitable as a pre-render gate.
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
RENDERER = HERE.parent
ROOT = RENDERER.parent
sys.path.insert(0, str(RENDERER))

from routing_geometry import route_points  # noqa: E402

SEMANTIC = ROOT / "visio-spec" / "pages" / "p1_uc_overview.yaml"
CANDIDATE = RENDERER / "phase1-routing-rc6-candidate.yaml"
REPORT = HERE / "out" / "P1_UC_ROUTE_CONTACT-AUDIT.json"

EPS = 1e-8
MIN_SEGMENT_CM = 0.10


def orientation(a, b):
    if abs(a[1] - b[1]) <= EPS:
        return "H"
    if abs(a[0] - b[0]) <= EPS:
        return "V"
    return "D"


def is_endpoint(point, segment):
    return any(
        abs(point[0] - q[0]) <= EPS and abs(point[1] - q[1]) <= EPS
        for q in segment
    )


def classify_contact(a, b, c, d):
    """Return one closed-segment contact classification, or None."""
    o1 = orientation(a, b)
    o2 = orientation(c, d)
    if "D" in (o1, o2):
        return None

    if o1 == o2 == "H":
        if abs(a[1] - c[1]) > EPS:
            return None
        lo = max(min(a[0], b[0]), min(c[0], d[0]))
        hi = min(max(a[0], b[0]), max(c[0], d[0]))
        if hi < lo - EPS:
            return None
        if hi - lo > EPS:
            return {"type": "overlap", "from": [lo, a[1]], "to": [hi, a[1]]}
        p = (lo, a[1])
        one_interior = is_endpoint(p, (a, b)) ^ is_endpoint(p, (c, d))
        return {"type": "tjunction" if one_interior else "shared_endpoint", "point": list(p)}

    if o1 == o2 == "V":
        if abs(a[0] - c[0]) > EPS:
            return None
        lo = max(min(a[1], b[1]), min(c[1], d[1]))
        hi = min(max(a[1], b[1]), max(c[1], d[1]))
        if hi < lo - EPS:
            return None
        if hi - lo > EPS:
            return {"type": "overlap", "from": [a[0], lo], "to": [a[0], hi]}
        p = (a[0], lo)
        one_interior = is_endpoint(p, (a, b)) ^ is_endpoint(p, (c, d))
        return {"type": "tjunction" if one_interior else "shared_endpoint", "point": list(p)}

    if o1 == "V":
        return classify_contact(c, d, a, b)

    # First segment horizontal, second vertical.
    x = c[0]
    y = a[1]
    if not (
        min(a[0], b[0]) - EPS <= x <= max(a[0], b[0]) + EPS
        and min(c[1], d[1]) - EPS <= y <= max(c[1], d[1]) + EPS
    ):
        return None

    p = (x, y)
    e1 = is_endpoint(p, (a, b))
    e2 = is_endpoint(p, (c, d))
    if not e1 and not e2:
        kind = "crossing"
    elif e1 ^ e2:
        kind = "tjunction"
    else:
        kind = "shared_endpoint"
    return {"type": kind, "point": list(p)}


def contact_key(item):
    if item["type"] == "overlap":
        return (
            item["type"],
            tuple(round(float(v), 6) for v in item["from"]),
            tuple(round(float(v), 6) for v in item["to"]),
        )
    return (
        item["type"],
        tuple(round(float(v), 6) for v in item["point"]),
    )


def collinear_redundant(a, b, c):
    same_x = abs(a[0] - b[0]) <= EPS and abs(b[0] - c[0]) <= EPS
    same_y = abs(a[1] - b[1]) <= EPS and abs(b[1] - c[1]) <= EPS
    between = (
        min(a[0], c[0]) - EPS <= b[0] <= max(a[0], c[0]) + EPS
        and min(a[1], c[1]) - EPS <= b[1] <= max(a[1], c[1]) + EPS
    )
    return (same_x or same_y) and between


def main():
    sem = yaml.safe_load(SEMANTIC.read_text(encoding="utf-8"))
    cand = yaml.safe_load(CANDIDATE.read_text(encoding="utf-8"))

    nodes = {s["id"]: s for s in sem["shapes"] if s["id"] != "BOUNDARY"}
    routes = {r["id"]: r for r in cand["routes"]}
    paths = {rid: route_points(route, nodes) for rid, route in routes.items()}

    ids = list(paths)
    contacts = []
    contact_pairs = set()

    for i, route_a in enumerate(ids):
        segments_a = list(zip(paths[route_a], paths[route_a][1:]))
        for route_b in ids[i + 1:]:
            segments_b = list(zip(paths[route_b], paths[route_b][1:]))
            seen = set()
            for ia, (a, b) in enumerate(segments_a):
                for ib, (c, d) in enumerate(segments_b):
                    item = classify_contact(a, b, c, d)
                    if item is None:
                        continue
                    key = contact_key(item)
                    if key in seen:
                        continue
                    seen.add(key)
                    contact_pairs.add((route_a, route_b))
                    contacts.append({
                        "routeA": route_a,
                        "routeB": route_b,
                        "segmentA": ia,
                        "segmentB": ib,
                        **item,
                    })

    # Self-contact gate: cross-route cleanliness is insufficient if one
    # Association folds back into itself.  Adjacent segments share their
    # normal bend and are ignored; every non-adjacent contact is a defect.
    self_contacts = []
    for rid, points in paths.items():
        segments = list(zip(points, points[1:]))
        for ia, (a, b) in enumerate(segments):
            for ib in range(ia + 2, len(segments)):
                c, d = segments[ib]
                item = classify_contact(a, b, c, d)
                if item is None:
                    continue
                self_contacts.append({
                    "route": rid,
                    "segmentA": ia,
                    "segmentB": ib,
                    **item,
                })

    short_segments = []
    redundant_points = []
    for rid, points in paths.items():
        for index, (a, b) in enumerate(zip(points, points[1:])):
            length = math.hypot(b[0] - a[0], b[1] - a[1])
            if length + EPS < MIN_SEGMENT_CM:
                short_segments.append({
                    "route": rid,
                    "segment": index,
                    "lengthCm": length,
                    "from": list(a),
                    "to": list(b),
                })
        for index in range(1, len(points) - 1):
            if collinear_redundant(points[index - 1], points[index], points[index + 1]):
                redundant_points.append({
                    "route": rid,
                    "pointIndex": index,
                    "point": list(points[index]),
                })

    counts = {}
    for item in contacts:
        counts[item["type"]] = counts.get(item["type"], 0) + 1
    self_counts = {}
    for item in self_contacts:
        self_counts[item["type"]] = self_counts.get(item["type"], 0) + 1

    payload = {
        "pageName": cand["pageName"],
        "status": "PASS" if not contacts and not self_contacts and not short_segments and not redundant_points else "FAIL",
        "routeCount": len(paths),
        "contactPairCount": len(contact_pairs),
        "uniqueContactCount": len(contacts),
        "contactCounts": {
            "crossing": counts.get("crossing", 0),
            "overlap": counts.get("overlap", 0),
            "tjunction": counts.get("tjunction", 0),
            "shared_endpoint": counts.get("shared_endpoint", 0),
        },
        "selfContactCount": len(self_contacts),
        "selfContactCounts": {
            "crossing": self_counts.get("crossing", 0),
            "overlap": self_counts.get("overlap", 0),
            "tjunction": self_counts.get("tjunction", 0),
            "shared_endpoint": self_counts.get("shared_endpoint", 0),
        },
        "minimumSegmentCm": MIN_SEGMENT_CM,
        "shortSegmentCount": len(short_segments),
        "redundantCollinearPointCount": len(redundant_points),
        "contacts": contacts,
        "selfContacts": self_contacts,
        "shortSegments": short_segments,
        "redundantCollinearPoints": redundant_points,
        "failures": (
            ([] if not contacts else [f"{len(contacts)} cross-route contacts"])
            + ([] if not self_contacts else [f"{len(self_contacts)} self-route contacts"])
            + ([] if not short_segments else [f"{len(short_segments)} segments shorter than {MIN_SEGMENT_CM} cm"])
            + ([] if not redundant_points else [f"{len(redundant_points)} redundant collinear route points"])
        ),
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=True, indent=2))
    return 0 if payload["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
