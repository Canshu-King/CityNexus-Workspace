#!/usr/bin/env python3
"""Find the smallest near-complete route subset whose removal makes B06 reachable."""
from __future__ import annotations

import argparse
import copy
import itertools
import json
from pathlib import Path

import yaml

from explore_p1_disjoint_pool import _candidate_points_cm, _candidate_pool
from route_p1_negotiated_grid import build_axes, build_graph, load
from routing_geometry import route_points

PLAN = "PLAN_QUOTA_SAVER_DUAL_ROTATED_20260908"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--near", type=Path, required=True)
    parser.add_argument("--fixed-routes", type=Path, required=True)
    parser.add_argument("--samples", type=int, default=6)
    parser.add_argument("--json-out", type=Path, required=True)
    args = parser.parse_args()

    near = json.loads(args.near.read_text(encoding="utf-8"))
    sem, _original, nodes, routes, _overrides, frozen, _mutable = load(PLAN)
    witness = yaml.safe_load(args.fixed_routes.read_text(encoding="utf-8")) or {}
    for supplied in witness.get("routes", []):
        merged = copy.deepcopy(routes[supplied["id"]])
        merged.update({key: copy.deepcopy(value) for key, value in supplied.items() if key != "id"})
        frozen[f"seed:{supplied['id']}"] = route_points(merged, nodes)
    for rid, data in near["routes"].items():
        for key in ("sourcePortFraction", "targetSide", "targetPortFraction"):
            routes[rid][key] = data[key]

    occupied = {
        rid: data["points"] for rid, data in near["routes"].items()
        if data.get("points") is not None
    }
    blocker_ids = sorted(occupied)
    rows = []
    for size in (0, 1, 2, 3):
        for removed in itertools.combinations(blocker_ids, size):
            hard = dict(frozen)
            for rid, points in occupied.items():
                if rid not in removed:
                    hard[f"near:{rid}"] = points
            route = routes["A-B-06"]
            xs, ys = build_axes(sem, [route], nodes, hard)
            ix, iy, allowed = build_graph(xs, ys, nodes, hard)
            pool = _candidate_pool(
                route, nodes, xs, ys, ix, iy, allowed,
                args.samples, 2026090800 + sum(sum(map(ord, rid)) for rid in removed),
            )
            row = {
                "removed": list(removed),
                "candidateCount": len(pool),
                "candidates": [_candidate_points_cm(candidate) for candidate in pool[:4]],
            }
            rows.append(row)
            if pool:
                payload = {"status": "PASS", "minimumRemovalSize": size, "rows": rows}
                args.json_out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
                print(json.dumps(payload, ensure_ascii=False, indent=2))
                return 0
    payload = {"status": "FAIL", "rows": rows}
    args.json_out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
