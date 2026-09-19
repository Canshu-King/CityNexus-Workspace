#!/usr/bin/env python3
"""Generate exact candidate pools for the four-route near-witness blocker cluster."""
from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path

import yaml

from explore_p1_disjoint_pool import _candidate_points_cm, _candidate_pool
from route_p1_negotiated_grid import build_axes, build_graph, load
from routing_geometry import route_points

PLAN = "PLAN_QUOTA_SAVER_DUAL_ROTATED_20260908"
CLUSTER = ("A-B-06", "A-PA-07", "A-CD-UC-10", "A-M-UC-10")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--fixed-routes", type=Path, required=True)
    parser.add_argument("--route-overrides", type=Path, required=True)
    parser.add_argument("--samples", type=int, default=18)
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--json-out", type=Path, required=True)
    args = parser.parse_args()

    sem, _original, nodes, routes, _overrides, frozen, _mutable = load(PLAN)
    fixed = yaml.safe_load(args.fixed_routes.read_text(encoding="utf-8")) or {}
    for supplied in fixed.get("routes", []):
        merged = copy.deepcopy(routes[supplied["id"]])
        merged.update({key: copy.deepcopy(value) for key, value in supplied.items() if key != "id"})
        frozen[f"seed:{supplied['id']}"] = route_points(merged, nodes)
    overrides = yaml.safe_load(args.route_overrides.read_text(encoding="utf-8")) or {}
    for rid, supplied in overrides.get("routes", {}).items():
        routes[rid].update(copy.deepcopy(supplied))

    local = [routes[rid] for rid in CLUSTER]
    xs, ys = build_axes(sem, local, nodes, frozen)
    ix, iy, allowed = build_graph(xs, ys, nodes, frozen)
    pools = {}
    for index, rid in enumerate(CLUSTER):
        candidates = _candidate_pool(
            routes[rid], nodes, xs, ys, ix, iy, allowed,
            args.samples, args.seed + index * 100003,
        )
        pools[rid] = [
            {
                "points": _candidate_points_cm(candidate),
                "cost": candidate.cost,
                "family": candidate.family,
            }
            for candidate in candidates
        ]
    payload = {
        "status": "POOL", "seed": args.seed,
        "candidateCounts": {rid: len(values) for rid, values in pools.items()},
        "candidatePools": pools,
    }
    args.json_out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(payload["candidateCounts"], ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
