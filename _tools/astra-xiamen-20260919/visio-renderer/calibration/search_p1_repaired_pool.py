"""Non-OR-Tools end-to-end feasibility search over a repaired candidate pool.

Pipeline:
  topology pre-gate -> diversified route pools -> targeted pair-gap repair ->
  pairwise pool feasibility -> exact MRV/LCV first-solution CSP -> staging YAML.

This is a search workbench only.  It never edits the authoritative candidate
and a staging PASS is not promotable until the official V1/Contact/V2/V3/full
pytest gates pass against that staging file.
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

from explore_p1_disjoint_pool import (
    _candidate_pool,
    _path_cost,
    _repair_pairwise_gaps,
)
from route_candidate_selector import (
    arc_consistency_prune,
    build_conflicts,
    find_first_solution,
    make_candidate,
    route_pair_compatibility,
)
from route_p1_negotiated_grid import build_axes, build_graph, load, topology_gate
from routing_geometry import route_points

OUT = HERE / "out"
STAGING = OUT / "P1-REPAIRED-POOL-STAGING.yaml"
TRACE = OUT / "P1-REPAIRED-POOL-TRACE.json"


def run(*, plan, samples, seed, traveler_skeleton, pair_repair_rounds,
        pair_synth_samples, pair_fixed_limit, search_seconds):
    sem, original, nodes, routes, overrides, frozen, mutable = load(plan)
    xs, ys = build_axes(sem, mutable, nodes, frozen)
    ix, iy, allowed = build_graph(xs, ys, nodes, frozen)

    skeleton_by_id = {}
    if traveler_skeleton is not None:
        doc = yaml.safe_load(traveler_skeleton.read_text(encoding="utf-8")) or {}
        skeleton_by_id = {item.get("id"): item for item in doc.get("routes", [])}

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
                    "routeId": route["id"], "family": "validated-skeleton",
                    "points": points, "cost": _path_cost(points),
                    "tag": f"{route['id']}:validated-skeleton",
                }))
            except (KeyError, ValueError):
                pass
        unique = {}
        for candidate in values:
            old = unique.get(candidate.points)
            if old is None or candidate.cost < old.cost:
                unique[candidate.points] = candidate
        pools[route["id"]] = list(unique.values())

    repair_history = _repair_pairwise_gaps(
        pools=pools, routes=mutable, nodes=nodes, xs=xs, ys=ys, frozen=frozen,
        rounds=pair_repair_rounds, synth_samples=pair_synth_samples,
        fixed_limit=pair_fixed_limit, seed=seed,
    )

    conflicts = build_conflicts(pools)
    pair_rows = route_pair_compatibility(pools, conflicts=conflicts)
    impossible = [row for row in pair_rows if row["compatiblePairs"] == 0]
    topology = topology_gate(plan)
    payload = {
        "status": "FAIL",
        "plan": plan,
        "topologyGateStatus": topology["status"],
        "orientableGenus": topology["orientableGenus"],
        "candidateCount": sum(len(values) for values in pools.values()),
        "familyCounts": {rid: len(values) for rid, values in pools.items()},
        "conflictPairCount": sum(len(values) for values in conflicts.values()) // 2,
        "pairRepairHistory": repair_history,
        "impossibleRoutePairs": impossible,
        "authoritativeCandidateModified": False,
    }
    if impossible:
        payload["reason"] = "pairwise-impossible-current-pool"
        OUT.mkdir(parents=True, exist_ok=True)
        TRACE.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 2

    ac3 = arc_consistency_prune(pools, conflicts=conflicts)
    payload["arcConsistency"] = {
        "status": ac3["status"],
        "rounds": ac3["rounds"],
        "emptyRoutes": ac3["emptyRoutes"],
        "removalCount": len(ac3["removals"]),
        "lastRemovals": ac3["removals"][-30:],
        "remainingDomainSizes": {rid: len(values) for rid, values in ac3["domains"].items()},
    }
    if ac3["status"] != "PASS":
        payload["reason"] = "arc-consistency-proved-current-pool-infeasible"
        OUT.mkdir(parents=True, exist_ok=True)
        TRACE.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 2

    pruned = ac3["domains"]
    pruned_conflicts = build_conflicts(pruned)
    result = find_first_solution(
        pruned, conflicts=pruned_conflicts, time_limit_seconds=search_seconds,
    )
    payload["csp"] = {
        key: value for key, value in result.items() if key != "selection"
    }
    if result["status"] != "PASS":
        payload["reason"] = "no-complete-selection-found"
        OUT.mkdir(parents=True, exist_ok=True)
        TRACE.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 2

    selection = result["selection"]
    staged = copy.deepcopy(original)
    staged["metadata"]["status"] = "STAGING_GEOMETRY_CANDIDATE"
    for route in staged["routes"]:
        rid = route["id"]
        candidate = selection.get(rid)
        if candidate is None:
            continue
        route.update(overrides.get(rid, {}))
        route["waypoints"] = [
            [round(x / 200.0, 2), round(y / 200.0, 2)]
            for x, y in candidate.points[1:-1]
        ]
        route["planningStatus"] = "ROUTE_PLANNED_PENDING_EXTERNAL_FREEZE"

    OUT.mkdir(parents=True, exist_ok=True)
    STAGING.write_text(yaml.safe_dump(staged, sort_keys=False), encoding="utf-8")
    payload.update({
        "status": "PASS",
        "reason": "complete-contact-free-pool-selection",
        "stagingCandidate": str(STAGING),
        "selection": {
            rid: {"key": candidate.key, "family": candidate.family, "cost": candidate.cost}
            for rid, candidate in sorted(selection.items())
        },
    })
    TRACE.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--plan", default="PLAN_TRAVELER_SKELETON_PLANAR_GRID")
    parser.add_argument("--samples", type=int, default=4)
    parser.add_argument("--seed", type=int, default=20260908)
    parser.add_argument("--traveler-skeleton", type=Path)
    parser.add_argument("--pair-repair-rounds", type=int, default=2)
    parser.add_argument("--pair-synth-samples", type=int, default=3)
    parser.add_argument("--pair-fixed-limit", type=int, default=3)
    parser.add_argument("--search-seconds", type=float, default=60.0)
    args = parser.parse_args()
    return run(**vars(args))


if __name__ == "__main__":
    raise SystemExit(main())
