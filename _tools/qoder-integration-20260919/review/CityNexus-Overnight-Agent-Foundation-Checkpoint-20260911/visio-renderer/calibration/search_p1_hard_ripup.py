"""Randomized hard-obstacle rip-up search over the global P1 grid."""
from __future__ import annotations

import argparse
import copy
import json
import random
import sys

import yaml

from route_p1_negotiated_grid import (
    FROZEN, OUT, STAGING, TRACE, astar, build_axes, build_graph, compact,
    load, path_resources,
)


def run(plan_id, trials, seed, bend_cost):
    sem, original, nodes, routes, overrides, frozen, mutable = load(plan_id)
    xs, ys = build_axes(sem, mutable, nodes, frozen)
    ix, iy, allowed = build_graph(xs, ys, nodes, frozen)
    ids = [r["id"] for r in mutable]
    by_id = {r["id"]: r for r in mutable}
    base = [
        "A-T-UC-07", "A-T-UC-06", "A-M-UC-08", "A-CE-09",
        "A-M-UC-10", "A-CD-UC-10", "A-PA-07", "A-B-06",
    ]
    best = {"routed": 0, "fail": None, "trial": None}
    for trial in range(trials):
        rng = random.Random(seed + trial * 104729)
        order = ids[:]
        if trial % 4 == 0:
            order = base + [rid for rid in order if rid not in base]
        elif trial % 4 == 1:
            order = list(reversed(base)) + [rid for rid in order if rid not in base]
        else:
            rng.shuffle(order)
        vertex_use = __import__("collections").Counter()
        edge_use = __import__("collections").Counter()
        paths = {}
        failure = None
        for rid in order:
            path = astar(by_id[rid], nodes, xs, ys, ix, iy, allowed,
                         vertex_use, edge_use, __import__("collections").Counter(),
                         __import__("collections").Counter(), 0.0, bend_cost, rng, hard=True, noise=0.45)
            if path is None:
                failure = rid; break
            paths[rid] = path
            vertices, edges = path_resources(path, xs, ys)
            vertex_use.update(vertices); edge_use.update(edges)
        if len(paths) > best["routed"]:
            best = {"routed": len(paths), "fail": failure, "trial": trial, "order": order}
            print(json.dumps({"trial": trial, **best}, ensure_ascii=False), flush=True)
        if len(paths) != len(ids):
            continue
        staged = copy.deepcopy(original)
        staged["metadata"]["status"] = "STAGING_GEOMETRY_CANDIDATE"
        for route in staged["routes"]:
            rid = route["id"]
            if rid not in paths:
                continue
            route.update(overrides.get(rid, {}))
            route["waypoints"] = [[round(x, 2), round(y, 2)] for x, y in compact(paths[rid])[1:-1]]
            route["planningStatus"] = "ROUTE_PLANNED_PENDING_EXTERNAL_FREEZE"
        OUT.mkdir(parents=True, exist_ok=True)
        STAGING.write_text(yaml.safe_dump(staged, sort_keys=False), encoding="utf-8")
        payload = {"status": "PASS", "plan": plan_id, "trial": trial, "order": order,
                   "axisCounts": {"x": len(xs), "y": len(ys)},
                   "stagingCandidate": str(STAGING), "authoritativeCandidateModified": False,
                   "frozenExtendIds": sorted(FROZEN)}
        TRACE.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return payload
    payload = {"status": "FAIL", "plan": plan_id, "trials": trials, "best": best,
               "axisCounts": {"x": len(xs), "y": len(ys)},
               "authoritativeCandidateModified": False, "frozenExtendIds": sorted(FROZEN)}
    TRACE.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return payload


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--plan", default="PLAN_O_GRID10_NEGOTIATED")
    p.add_argument("--trials", type=int, default=500)
    p.add_argument("--seed", type=int, default=20260907)
    p.add_argument("--bend-cost", type=float, default=0.3)
    args = p.parse_args()
    result = run(args.plan, args.trials, args.seed, args.bend_cost)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
