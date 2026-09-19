"""Topology-safe candidate-pool gap diagnostic for P1 Association routing.

This tool deliberately does not require OR-Tools.  It answers a cheaper and
more actionable question before CP-SAT: does the current discrete path pool
contain *any* mutually compatible candidate pair for every pair of routes?

If ``compatiblePairs == 0`` for a route pair, the current pool cannot possibly
produce an 18/18 solution.  Generate new homotopy families for those routes
instead of spending more solver time on the same pool.
"""
from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
import sys

import yaml

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent), str(HERE)]

from explore_p1_disjoint_pool import _candidate_pool, _path_cost
from route_candidate_selector import build_conflicts, make_candidate, route_pair_compatibility
from route_p1_negotiated_grid import build_axes, build_graph, load, topology_gate
from routing_geometry import route_points


def run(*, plan, samples, seed, traveler_skeleton, output):
    sem, _, nodes, routes, _, frozen, mutable = load(plan)
    xs, ys = build_axes(sem, mutable, nodes, frozen)
    ix, iy, allowed = build_graph(xs, ys, nodes, frozen)

    skeleton_by_id = {}
    if traveler_skeleton is not None:
        document = yaml.safe_load(traveler_skeleton.read_text(encoding="utf-8")) or {}
        skeleton_by_id = {item.get("id"): item for item in document.get("routes", [])}

    pools = {}
    for route in mutable:
        route_seed = seed + sum(ord(ch) for ch in route["id"]) * 100003
        values = _candidate_pool(route, nodes, xs, ys, ix, iy, allowed, samples, route_seed)
        supplied = skeleton_by_id.get(route["id"])
        if supplied is not None and route.get("family") == "traveler":
            with_skeleton = copy.deepcopy(route)
            with_skeleton["waypoints"] = copy.deepcopy(supplied.get("waypoints", []))
            points = route_points(with_skeleton, nodes)
            try:
                values.append(make_candidate({
                    "routeId": route["id"],
                    "family": "validated-skeleton",
                    "points": points,
                    "cost": _path_cost(points),
                    "tag": f"{route['id']}:validated-skeleton",
                }))
            except (KeyError, ValueError):
                pass
        # Geometry, not a random tag, defines a unique choice.
        unique = {}
        for candidate in values:
            previous = unique.get(candidate.points)
            if previous is None or candidate.cost < previous.cost:
                unique[candidate.points] = candidate
        pools[route["id"]] = sorted(unique.values(), key=lambda c: (c.cost, c.key))

    empty = sorted(rid for rid, values in pools.items() if not values)
    conflicts = build_conflicts(pools) if not empty else {}
    pair_rows = route_pair_compatibility(pools, conflicts=conflicts) if not empty else []
    impossible = [row for row in pair_rows if row["compatiblePairs"] == 0]
    tight = sorted(
        [row for row in pair_rows if 0 < row["compatibilityRatio"] < 0.05],
        key=lambda row: (row["compatibilityRatio"], row["routeA"], row["routeB"]),
    )
    topology = topology_gate(plan)
    payload = {
        "status": "PASS" if not empty and not impossible else "FAIL",
        "meaning": (
            "PASS means only that the current discrete pool has no pairwise-impossible route pair; "
            "it does not prove that one global 18-route selection exists."
        ),
        "plan": plan,
        "topologyGateStatus": topology["status"],
        "orientableGenus": topology["orientableGenus"],
        "samplesPerRoute": samples,
        "seed": seed,
        "axisCounts": {"x": len(xs), "y": len(ys)},
        "candidateCount": sum(len(values) for values in pools.values()),
        "familyCounts": {rid: len(values) for rid, values in pools.items()},
        "emptyRoutes": empty,
        "conflictPairCount": sum(len(values) for values in conflicts.values()) // 2,
        "impossibleRoutePairs": impossible,
        "tightRoutePairs": tight[:50],
        "authoritativeCandidateModified": False,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if payload["status"] == "PASS" else 2


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--plan", default="PLAN_TRAVELER_SKELETON_PLANAR_GRID")
    parser.add_argument("--samples", type=int, default=32)
    parser.add_argument("--seed", type=int, default=20260908)
    parser.add_argument("--traveler-skeleton", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    return run(**vars(args))


if __name__ == "__main__":
    raise SystemExit(main())
