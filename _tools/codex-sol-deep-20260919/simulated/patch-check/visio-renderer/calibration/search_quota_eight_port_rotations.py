#!/usr/bin/env python3
"""Search genus-zero port allocations and hard-route the quota-saver eight-route cluster."""
from __future__ import annotations

import argparse
import copy
import json
import math
import random
from collections import Counter, defaultdict
from pathlib import Path

import yaml

from plan_p1_associations import compact
from explore_p1_disjoint_pool import _candidate_pool, _field
from route_candidate_selector import (
    arc_consistency_prune, build_conflicts, find_first_solution, make_candidate,
)
from route_p1_negotiated_grid import (
    astar, build_axes, build_graph, load, path_resources, topology_gate,
)
from routing_geometry import route_points
from search_p1_global_port_rotations import genus, perimeter, target_options

PLAN = "PLAN_QUOTA_SAVER_DUAL_ROTATED_20260908"
CLUSTER = (
    "A-B-06", "A-PA-07", "A-CE-09", "A-CD-UC-10",
    "A-M-UC-08", "A-M-UC-10", "A-CD-UC-04", "A-M-UC-04",
)


def source_fractions(node):
    top = float(node["y"]) - float(node["height"]) / 2.0
    height = float(node["height"])
    first = math.ceil((top + 0.05) * 10.0) / 10.0
    last = math.floor((top + height - 0.05) * 10.0) / 10.0
    result = []
    y = first
    while y <= last + 1e-9:
        result.append((y - top) / height)
        y = round(y + 0.1, 10)
    return result


def exact_conflicts(paths):
    pools = {}
    for rid, points in paths.items():
        try:
            pools[rid] = [make_candidate({
                "routeId": rid, "family": "port-rotation-hard",
                "points": points, "cost": 0.0, "tag": rid,
            })]
        except ValueError as exc:
            return {"self": [{"route": rid, "error": str(exc)}], "pairs": []}
    conflicts = build_conflicts(pools)
    pairs = set()
    for rid, values in pools.items():
        for other in conflicts[values[0].key]:
            pairs.add(tuple(sorted((rid, other.split(":", 1)[0]))))
    return {"self": [], "pairs": [list(pair) for pair in sorted(pairs)]}


def repair_near_complete(routes, nodes, xs, ys, ix, iy, allowed, partial_paths, seed, samples):
    pools = {}
    for index, rid in enumerate(CLUSTER):
        pool = _candidate_pool(
            routes[rid], nodes, xs, ys, ix, iy, allowed,
            samples, seed + index * 100003,
        )
        existing = partial_paths.get(rid)
        if existing:
            try:
                pool.append(make_candidate({
                    "routeId": rid, "family": "near-complete-existing",
                    "points": compact(existing), "cost": 0.0,
                    "tag": f"{rid}:existing",
                }))
            except ValueError:
                pass
        unique = {}
        for candidate in pool:
            old = unique.get(candidate.points)
            if old is None or candidate.cost < old.cost:
                unique[candidate.points] = candidate
        pools[rid] = list(unique.values())
    if any(not values for values in pools.values()):
        return None
    conflicts = build_conflicts(pools)
    ac3 = arc_consistency_prune(pools, conflicts=conflicts)
    if ac3["status"] != "PASS":
        return None
    result = find_first_solution(
        ac3["domains"], conflicts=build_conflicts(ac3["domains"]),
        time_limit_seconds=8.0,
    )
    if result["status"] != "PASS":
        return None
    return {
        rid: [[x / 200.0, y / 200.0] for x, y in candidate.points]
        for rid, candidate in result["selection"].items()
    }


def randomize_ports(routes, nodes, mutable_ids, rng):
    mutable = set(mutable_ids)
    by_source = defaultdict(list)
    by_target = defaultdict(list)
    for rid in mutable_ids:
        by_source[routes[rid]["source"]].append(rid)
        by_target[routes[rid]["target"]].append(rid)

    for source, ids in by_source.items():
        occupied = {
            round(float(route["sourcePortFraction"]), 12)
            for rid, route in routes.items()
            if rid not in mutable and route["source"] == source
        }
        choices = [value for value in source_fractions(nodes[source]) if round(value, 12) not in occupied]
        if len(choices) < len(ids):
            return False
        picked = rng.sample(choices, len(ids))
        for rid, fraction in zip(ids, picked):
            routes[rid]["sourcePortFraction"] = fraction

    for target, ids in by_target.items():
        occupied = [
            perimeter(nodes[target], route["targetSide"], route["targetPortFraction"])
            for rid, route in routes.items()
            if rid not in mutable and route["target"] == target
        ]
        choices = [
            item for item in target_options(nodes[target])
            if all(abs(perimeter(nodes[target], *item) - value) > 1e-8 for value in occupied)
        ]
        rng.shuffle(choices)
        picked = []
        for item in choices:
            value = perimeter(nodes[target], *item)
            if all(abs(value - perimeter(nodes[target], *old)) > 1e-8 for old in picked):
                picked.append(item)
            if len(picked) == len(ids):
                break
        if len(picked) != len(ids):
            return False
        rng.shuffle(ids)
        for rid, (side, fraction) in zip(ids, picked):
            routes[rid]["targetSide"] = side
            routes[rid]["targetPortFraction"] = fraction
    return True


def run(args):
    sem, original, nodes, base_routes, _overrides, frozen, _mutable = load(PLAN)
    witness = yaml.safe_load(args.fixed_routes.read_text(encoding="utf-8")) or {}
    witness_by_id = {route["id"]: route for route in witness.get("routes", [])}
    for rid, supplied in witness_by_id.items():
        base_routes[rid].update({key: copy.deepcopy(value) for key, value in supplied.items() if key != "id"})
        frozen[f"seed:{rid}"] = route_points(base_routes[rid], nodes)

    rng = random.Random(args.seed)
    topology_passes = 0
    routed_best = 0
    best = {}
    best_exact_score = 10**9
    for attempt in range(args.attempts):
        routes = copy.deepcopy(base_routes)
        if not randomize_ports(routes, nodes, list(CLUSTER), rng):
            continue
        current_genus = genus(routes, nodes)
        if current_genus != 0:
            continue
        topology_passes += 1
        local_routes = [routes[rid] for rid in CLUSTER]
        xs, ys = build_axes(sem, local_routes, nodes, frozen)
        ix, iy, allowed = build_graph(xs, ys, nodes, frozen)

        priority = None
        repair_attempted = False
        for trial in range(args.trials):
            order = list(CLUSTER)
            rng.shuffle(order)
            if priority in order:
                order.remove(priority)
                order.insert(0, priority)
            vertex_use, edge_use = Counter(), Counter()
            paths = {}
            failed = None
            for rid in order:
                terrain, edge_terrain = _field(
                    xs, ys, rng.randrange(1, 2**31 - 1),
                    rng.choice(("free", "top", "bottom", "left", "right", "cross")),
                )
                path = astar(
                    routes[rid], nodes, xs, ys, ix, iy, allowed,
                    vertex_use, edge_use, terrain, edge_terrain,
                    0.0, args.bend_cost, rng, hard=True, noise=0.01,
                )
                if path is None:
                    failed = rid
                    break
                paths[rid] = path
                vertices, edges = path_resources(path[1:-1], xs, ys)
                vertex_use.update(vertices)
                edge_use.update(edges)
            if len(paths) > routed_best:
                routed_best = len(paths)
                best = {
                    "attempt": attempt, "trial": trial, "routed": routed_best,
                    "failure": failed, "order": order,
                }
                print(json.dumps({"progress": best, "topologyPasses": topology_passes}), flush=True)
            if len(paths) == len(CLUSTER) - 1 and not repair_attempted:
                near = {
                    "attempt": attempt,
                    "trial": trial,
                    "failure": failed,
                    "effectiveGenus": current_genus,
                    "routes": {
                        rid: {
                            "sourcePortFraction": routes[rid]["sourcePortFraction"],
                            "targetSide": routes[rid]["targetSide"],
                            "targetPortFraction": routes[rid]["targetPortFraction"],
                            "points": (
                                [[round(x, 3), round(y, 3)] for x, y in compact(paths[rid])]
                                if rid in paths else None
                            ),
                        }
                        for rid in CLUSTER
                    },
                }
                args.json_out.with_suffix(".near.json").write_text(
                    json.dumps(near, ensure_ascii=False, indent=2), encoding="utf-8"
                )
                repair_attempted = True
                repaired = None
                if args.repair_samples > 0:
                    repaired = repair_near_complete(
                        routes, nodes, xs, ys, ix, iy, allowed, paths,
                        args.seed + attempt * 1000003 + trial * 7919,
                        args.repair_samples,
                    )
                if repaired is not None:
                    paths = repaired
                    failed = None
            if len(paths) != len(CLUSTER):
                priority = failed
                continue
            exact = exact_conflicts(paths)
            exact_score = len(exact["self"]) + len(exact["pairs"])
            if exact_score < best_exact_score:
                best_exact_score = exact_score
                diagnostic = {
                    "attempt": attempt,
                    "trial": trial,
                    "effectiveGenus": current_genus,
                    "exact": exact,
                    "routes": {
                        rid: {
                            "sourcePortFraction": routes[rid]["sourcePortFraction"],
                            "targetSide": routes[rid]["targetSide"],
                            "targetPortFraction": routes[rid]["targetPortFraction"],
                            "points": [[round(x, 3), round(y, 3)] for x, y in compact(paths[rid])],
                        }
                        for rid in CLUSTER
                    },
                }
                args.json_out.with_suffix(".exact.json").write_text(
                    json.dumps(diagnostic, ensure_ascii=False, indent=2), encoding="utf-8"
                )
                print(json.dumps({"exactProgress": exact_score, "attempt": attempt}), flush=True)
            if exact["self"] or exact["pairs"]:
                continue

            staged = copy.deepcopy(original)
            staged["metadata"]["status"] = "STAGING_GEOMETRY_CANDIDATE"
            for route in staged["routes"]:
                rid = route["id"]
                if rid in witness_by_id:
                    route.update({key: copy.deepcopy(value) for key, value in witness_by_id[rid].items() if key != "id"})
                    route["planningStatus"] = "ROUTE_PLANNED_PENDING_EXTERNAL_FREEZE"
                elif rid in paths:
                    route["sourcePortFraction"] = routes[rid]["sourcePortFraction"]
                    route["targetSide"] = routes[rid]["targetSide"]
                    route["targetPortFraction"] = routes[rid]["targetPortFraction"]
                    route["waypoints"] = [
                        [round(x, 3), round(y, 3)] for x, y in compact(paths[rid])[1:-1]
                    ]
                    route["planningStatus"] = "ROUTE_PLANNED_PENDING_EXTERNAL_FREEZE"
            args.staging_out.write_text(yaml.safe_dump(staged, sort_keys=False), encoding="utf-8")
            payload = {
                "status": "PASS", "plan": PLAN, "seed": args.seed,
                "attempt": attempt, "trial": trial, "topologyPasses": topology_passes,
                "effectiveGenus": 0, "routeCount": len(paths),
                "stagingCandidate": str(args.staging_out),
                "authoritativeCandidateModified": False,
            }
            args.json_out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
            return payload

    payload = {
        "status": "FAIL", "plan": PLAN, "seed": args.seed,
        "attempts": args.attempts, "topologyPasses": topology_passes,
        "best": best, "authoritativeCandidateModified": False,
    }
    args.json_out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return payload


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--fixed-routes", type=Path, required=True)
    parser.add_argument("--attempts", type=int, default=2000)
    parser.add_argument("--trials", type=int, default=12)
    parser.add_argument("--bend-cost", type=float, default=0.25)
    parser.add_argument("--repair-samples", type=int, default=12)
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--staging-out", type=Path, required=True)
    parser.add_argument("--json-out", type=Path, required=True)
    args = parser.parse_args()
    payload = run(args)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if payload["status"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
