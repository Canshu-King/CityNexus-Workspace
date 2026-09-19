"""Generate diversified full-route candidates and select an exact disjoint set."""
from __future__ import annotations

import argparse
import copy
import json
import random
import sys

import yaml
from ortools.sat.python import cp_model

from critical_grid_geometry import q
from route_candidate_selector import build_conflicts, make_candidate
from route_p1_negotiated_grid import (
    FROZEN, OUT, STAGING, TRACE, astar, build_axes, build_graph, compact, load,
)


def run(plan_id, samples, seconds, seed):
    sem, original, nodes, routes, overrides, frozen, mutable = load(plan_id)
    xs, ys = build_axes(sem, mutable, nodes, frozen)
    ix, iy, allowed = build_graph(xs, ys, nodes, frozen)
    pools = {}
    for number, route in enumerate(mutable):
        unique = {}
        for variant in range(samples):
            rng = random.Random(seed + number * 100003 + variant * 997)
            # A modest random cost changes equal/near-equal corridor choices
            # without turning this into an unbounded wandering walk.
            path = astar(route, nodes, xs, ys, ix, iy, allowed,
                         __import__("collections").Counter(), __import__("collections").Counter(),
                         __import__("collections").Counter(), __import__("collections").Counter(),
                         0.0, 0.05 + (variant % 7) * 0.25, rng, noise=0.015 + (variant % 5) * 0.015)
            if path is None:
                continue
            try:
                candidate = make_candidate({"routeId": route["id"], "family": f"pool-{variant}",
                                            "points": path, "cost": len(path)})
            except Exception:
                continue
            unique.setdefault(candidate.points, candidate)
        pools[route["id"]] = list(unique.values())
        print(json.dumps({"route": route["id"], "candidates": len(pools[route["id"]])}), flush=True)
    missing = [rid for rid, values in pools.items() if not values]
    if missing:
        payload = {"status": "FAIL", "reason": "empty candidate domain", "emptyRoutes": missing,
                   "familyCounts": {rid: len(v) for rid, v in pools.items()}}
        TRACE.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return payload
    conflicts = build_conflicts(pools)
    flat = [candidate for values in pools.values() for candidate in values]
    model = cp_model.CpModel()
    variables = {candidate.key: model.new_bool_var(f"c{index}") for index, candidate in enumerate(flat)}
    for rid, values in pools.items():
        model.add_exactly_one(variables[candidate.key] for candidate in values)
    pair_seen = set()
    for key, bad in conflicts.items():
        for other in bad:
            marker = tuple(sorted((key, other)))
            if marker in pair_seen:
                continue
            pair_seen.add(marker)
            model.add(variables[key] + variables[other] <= 1)
    model.minimize(sum(variables[c.key] * int(c.cost * 100) for c in flat))
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = seconds
    solver.parameters.num_search_workers = 8
    solver.parameters.random_seed = seed
    result = solver.solve(model)
    payload = {"status": "PASS" if result in (cp_model.OPTIMAL, cp_model.FEASIBLE) else "FAIL",
               "solverStatus": solver.status_name(result), "plan": plan_id,
               "familyCounts": {rid: len(v) for rid, v in pools.items()},
               "candidateCount": len(flat), "conflictPairCount": len(pair_seen),
               "wallTimeSeconds": solver.wall_time, "authoritativeCandidateModified": False,
               "frozenExtendIds": sorted(FROZEN)}
    if result not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        TRACE.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return payload
    selected = {rid: next(c for c in values if solver.boolean_value(variables[c.key])) for rid, values in pools.items()}
    staged = copy.deepcopy(original)
    staged["metadata"]["status"] = "STAGING_GEOMETRY_CANDIDATE"
    for route in staged["routes"]:
        candidate = selected.get(route["id"])
        if candidate is None:
            continue
        route.update(overrides.get(route["id"], {}))
        route["waypoints"] = [[round(x / 200, 2), round(y / 200, 2)] for x, y in candidate.points[1:-1]]
        route["planningStatus"] = "ROUTE_PLANNED_PENDING_EXTERNAL_FREEZE"
    OUT.mkdir(parents=True, exist_ok=True)
    STAGING.write_text(yaml.safe_dump(staged, sort_keys=False), encoding="utf-8")
    payload["stagingCandidate"] = str(STAGING)
    payload["selection"] = {rid: candidate.key for rid, candidate in selected.items()}
    TRACE.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return payload


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--plan", default="PLAN_O_GRID10_NEGOTIATED")
    p.add_argument("--samples", type=int, default=40)
    p.add_argument("--seconds", type=float, default=180.0)
    p.add_argument("--seed", type=int, default=20260907)
    args = p.parse_args()
    payload = run(args.plan, args.samples, args.seconds, args.seed)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if payload["status"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
