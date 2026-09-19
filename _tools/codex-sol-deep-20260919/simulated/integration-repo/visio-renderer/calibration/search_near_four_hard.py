#!/usr/bin/env python3
"""Hard sequential terrain search for the four-route near-witness blocker cluster."""
from __future__ import annotations

import argparse
import copy
import json
import random
from collections import Counter
from pathlib import Path

import yaml

from explore_p1_disjoint_pool import _field
from plan_p1_associations import compact
from route_candidate_selector import build_conflicts, make_candidate
from route_p1_negotiated_grid import astar, build_axes, build_graph, load, path_resources
from routing_geometry import route_points

PLAN = "PLAN_QUOTA_SAVER_DUAL_ROTATED_20260908"
BASE_CLUSTER = ("A-B-06", "A-PA-07", "A-CD-UC-10", "A-M-UC-10")
EXTRA_ROUTES = ("A-CE-09", "A-M-UC-08", "A-CD-UC-04", "A-M-UC-04")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--fixed-routes", type=Path, required=True)
    parser.add_argument("--route-overrides", type=Path, required=True)
    parser.add_argument("--near", type=Path)
    parser.add_argument("--release", action="append", dest="releases", choices=EXTRA_ROUTES)
    parser.add_argument("--trials", type=int, default=5000)
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
    cluster = list(BASE_CLUSTER)
    if args.near and args.releases:
        near = json.loads(args.near.read_text(encoding="utf-8"))
        for rid in args.releases:
            if rid not in cluster:
                cluster.append(rid)
        for rid in cluster:
            supplied = near["routes"][rid]
            for key in ("sourcePortFraction", "targetSide", "targetPortFraction"):
                routes[rid][key] = supplied[key]
        for rid in EXTRA_ROUTES:
            if rid in args.releases:
                continue
            frozen[f"near:{rid}"] = near["routes"][rid]["points"]
    local = [routes[rid] for rid in cluster]
    xs, ys = build_axes(sem, local, nodes, frozen)
    ix, iy, allowed = build_graph(xs, ys, nodes, frozen)
    rng = random.Random(args.seed)
    best = {"routed": 0}

    for trial in range(args.trials):
        order = list(cluster)
        rng.shuffle(order)
        # Systematically alternate the first commodity while retaining random
        # order for the remaining routes.
        first = cluster[trial % len(cluster)]
        order.remove(first)
        order.insert(0, first)
        vertex_use, edge_use = Counter(), Counter()
        paths = {}
        failure = None
        for index, rid in enumerate(order):
            terrain, edge_terrain = _field(
                xs, ys, rng.randrange(1, 2**31 - 1),
                ("free", "top", "bottom", "left", "right", "cross")[(trial + index) % 6],
            )
            path = astar(
                routes[rid], nodes, xs, ys, ix, iy, allowed,
                vertex_use, edge_use, terrain, edge_terrain,
                0.0, (0.10, 0.25, 0.50)[trial % 3], rng,
                hard=True, noise=0.01,
            )
            if path is None:
                failure = rid
                break
            paths[rid] = path
            vertices, edges = path_resources(path[1:-1], xs, ys)
            vertex_use.update(vertices)
            edge_use.update(edges)
        if len(paths) > best["routed"]:
            best = {"routed": len(paths), "trial": trial, "failure": failure, "order": order}
            print(json.dumps(best), flush=True)
        if len(paths) != len(cluster):
            continue
        pools = {}
        try:
            for rid, points in paths.items():
                pools[rid] = [make_candidate({
                    "routeId": rid, "points": compact(points), "cost": 0.0, "tag": rid,
                })]
        except ValueError:
            continue
        conflicts = build_conflicts(pools)
        if any(conflicts[candidate.key] for values in pools.values() for candidate in values):
            continue
        payload = {
            "status": "PASS", "trial": trial, "seed": args.seed,
            "selection": {
                rid: {"points": [[round(x, 3), round(y, 3)] for x, y in compact(points)]}
                for rid, points in paths.items()
            },
        }
        args.json_out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps(payload, ensure_ascii=False))
        return 0
    payload = {"status": "FAIL", "seed": args.seed, "best": best}
    args.json_out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False))
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
