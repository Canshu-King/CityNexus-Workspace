#!/usr/bin/env python3
"""Shardable topology-safe port/corridor search for the rescue 6-route cluster."""
from __future__ import annotations

import argparse
import copy
import json
import math
import sys
import time
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent), str(HERE)]

from explore_p1_disjoint_pool import (
    _candidate_points_cm, _candidate_pool, _merge_candidate, _path_cost,
    _repair_arc_empty_routes, _repair_pairwise_gaps,
)
from route_candidate_selector import (
    arc_consistency_prune,
    build_conflicts,
    candidates_contact,
    find_first_solution,
    make_candidate,
    route_pair_compatibility,
)
from route_p1_negotiated_grid import build_axes, build_graph, load
from routing_geometry import route_points
from search_p1_global_port_rotations import genus, target_options

PLAN = "PLAN_QUOTA_SAVER_DUAL_ROTATED_20260908"
CLUSTER = (
    "A-B-06", "A-PA-07", "A-CE-09",
    "A-CD-UC-10", "A-M-UC-08", "A-M-UC-10",
)
MISSING = ("A-CD-UC-10", "A-M-UC-08", "A-M-UC-10")


def exact_source_fractions(node):
    top = float(node["y"]) - float(node["height"]) / 2.0
    height = float(node["height"])
    first = math.ceil((top + 0.05) * 10.0) / 10.0
    last = math.floor((top + height - 0.05) * 10.0) / 10.0
    values = []
    y = first
    while y <= last + 1e-9:
        values.append((y - top) / height)
        y = round(y + 0.1, 10)
    return values


def add_witness_candidate(pool, route, nodes, raw, tag):
    if raw is None:
        return
    supplied = copy.deepcopy(route)
    supplied.update({k: copy.deepcopy(v) for k, v in raw.items() if k != "id"})
    try:
        points = route_points(supplied, nodes)
        candidate = make_candidate({
            "routeId": route["id"], "family": "partial15c",
            "points": points, "cost": _path_cost(points), "tag": tag,
        })
    except (KeyError, ValueError):
        return
    _merge_candidate(pool, candidate)


def run(args):
    sem, _original, nodes, routes, _overrides, frozen, _mutable = load(PLAN)
    witness = yaml.safe_load(args.fixed_routes.read_text(encoding="utf-8")) or {}
    witness_by_id = {item["id"]: item for item in witness.get("routes", [])}
    for rid, raw in witness_by_id.items():
        supplied = copy.deepcopy(routes[rid])
        supplied.update({k: copy.deepcopy(v) for k, v in raw.items() if k != "id"})
        frozen[f"seed:{rid}"] = route_points(supplied, nodes)

    local_routes = [routes[rid] for rid in CLUSTER]
    xs, ys = build_axes(sem, local_routes, nodes, frozen)
    ix, iy, allowed = build_graph(xs, ys, nodes, frozen)
    pools = {}
    started = time.monotonic()
    for rid in CLUSTER[1:]:
        route_seed = args.seed + sum(map(ord, rid)) * 100003
        pool = _candidate_pool(routes[rid], nodes, xs, ys, ix, iy, allowed,
                               args.route_samples, route_seed)
        add_witness_candidate(pool, routes[rid], nodes, witness_by_id.get(rid),
                              f"witness:{rid}")
        pools[rid] = pool

    b06 = routes["A-B-06"]
    target_values = target_options(nodes[b06["target"]])
    natural_rank = {"RIGHT": 0, "TOP": 1, "BOTTOM": 2, "LEFT": 3}
    target_values.sort(key=lambda item: (natural_rank[item[0]], abs(float(item[1]) - 0.5)))
    all_source_values = exact_source_fractions(nodes[b06["source"]])
    source_targets = (0.10, 0.25, 0.50, 0.75, 0.90)
    source_values = []
    for target in source_targets:
        value = min(all_source_values, key=lambda item: abs(item - target))
        if value not in source_values:
            source_values.append(value)
    variants = []
    for source_fraction in source_values:
        for target_side, target_fraction in target_values:
            changed = copy.deepcopy(routes)
            changed["A-B-06"]["sourcePortFraction"] = source_fraction
            changed["A-B-06"]["targetSide"] = target_side
            changed["A-B-06"]["targetPortFraction"] = target_fraction
            if genus(changed, nodes) == 0:
                variants.append((source_fraction, target_side, target_fraction))
    variants = variants[args.shard_index::args.shard_count]

    pa = routes["A-PA-07"]
    pa_target_values = []
    for side in ("RIGHT", "TOP", "BOTTOM"):
        options = [item for item in target_options(nodes[pa["target"]]) if item[0] == side]
        for wanted in (0.20, 0.50, 0.80):
            value = min(options, key=lambda item: abs(float(item[1]) - wanted))
            if value not in pa_target_values:
                pa_target_values.append(value)
    pa_sources_all = exact_source_fractions(nodes[pa["source"]])
    pa_source_values = []
    for wanted in (0.25, 0.50, 0.75):
        value = min(pa_sources_all, key=lambda item: abs(item - wanted))
        if value not in pa_source_values:
            pa_source_values.append(value)
    pa_variants = []
    for source_fraction in pa_source_values:
        for target_side, target_fraction in pa_target_values:
            pa_variants.append((source_fraction, target_side, target_fraction))

    b06_pool = []
    b06_ports = {}
    pa_ports = {}
    for pa_index, (pa_source, pa_side, pa_fraction) in enumerate(pa_variants):
        changed = copy.deepcopy(routes)
        changed["A-PA-07"]["sourcePortFraction"] = pa_source
        changed["A-PA-07"]["targetSide"] = pa_side
        changed["A-PA-07"]["targetPortFraction"] = pa_fraction
        if genus(changed, nodes) != 0:
            continue
        px, py = build_axes(sem, [changed["A-PA-07"]], nodes, frozen)
        pix, piy, pallowed = build_graph(px, py, nodes, frozen)
        generated_pa = _candidate_pool(
            changed["A-PA-07"], nodes, px, py, pix, piy, pallowed,
            args.port_samples,
            args.seed + args.shard_index * 1000003 + pa_index * 7919,
        )
        for candidate_index, pa_candidate in enumerate(generated_pa):
            try:
                pa_candidate = make_candidate({
                    "routeId": "A-PA-07", "family": "pa-port-search",
                    "points": _candidate_points_cm(pa_candidate),
                    "cost": pa_candidate.cost,
                    "tag": f"A-PA-07:port:{args.shard_index}:{pa_index}:{candidate_index}",
                })
            except ValueError:
                continue
            if _merge_candidate(pools["A-PA-07"], pa_candidate):
                pa_ports[pa_candidate.points] = {
                    "sourcePortFraction": pa_source,
                    "targetSide": pa_side,
                    "targetPortFraction": pa_fraction,
                }
    tested = 0
    for source_fraction, target_side, target_fraction in variants:
        if time.monotonic() - started >= args.seconds:
            break
        tested += 1
        route = copy.deepcopy(b06)
        route["sourcePortFraction"] = source_fraction
        route["targetSide"] = target_side
        route["targetPortFraction"] = target_fraction
        vx, vy = build_axes(sem, [route], nodes, frozen)
        vix, viy, vallowed = build_graph(vx, vy, nodes, frozen)
        generated = _candidate_pool(
            route, nodes, vx, vy, vix, viy, vallowed, args.port_samples,
            args.seed + tested * 7919 + args.shard_index * 104729,
        )
        for candidate_index, candidate in enumerate(generated):
            try:
                candidate = make_candidate({
                    "routeId": "A-B-06", "family": "b06-port-search",
                    "points": _candidate_points_cm(candidate), "cost": candidate.cost,
                    "tag": f"A-B-06:port:{args.shard_index}:{tested}:{candidate_index}",
                })
            except ValueError:
                continue
            if args.independent_pa:
                supported = True
                for rid in CLUSTER[1:]:
                    if any(not candidates_contact(candidate, other) for other in pools[rid]):
                        continue
                    hard = dict(frozen)
                    hard["__trial_b06__"] = _candidate_points_cm(candidate)
                    reroute = routes[rid]
                    rx, ry = build_axes(sem, [reroute], nodes, hard)
                    rix, riy, rallowed = build_graph(rx, ry, nodes, hard)
                    repairs = _candidate_pool(
                        reroute, nodes, rx, ry, rix, riy, rallowed,
                        args.pair_samples,
                        args.seed + tested * 100003 + candidate_index * 7919
                        + sum(map(ord, rid)) * 101,
                    )
                    compatible = []
                    for repair_index, repair in enumerate(repairs):
                        if candidates_contact(candidate, repair):
                            continue
                        try:
                            retagged = make_candidate({
                                "routeId": rid, "family": "b06-conditioned",
                                "points": _candidate_points_cm(repair),
                                "cost": repair.cost + 0.25,
                                "tag": f"{rid}:b06:{args.shard_index}:{tested}:{candidate_index}:{repair_index}",
                            })
                        except ValueError:
                            continue
                        compatible.append(retagged)
                    if not compatible:
                        supported = False
                        break
                    for repair in compatible:
                        _merge_candidate(pools[rid], repair)
                if not supported:
                    continue
                before = len(b06_pool)
                _merge_candidate(b06_pool, candidate)
                if len(b06_pool) > before:
                    b06_ports[candidate.points] = {
                        "sourcePortFraction": source_fraction,
                        "targetSide": target_side,
                        "targetPortFraction": target_fraction,
                    }
                continue
            hard_b06 = dict(frozen)
            hard_b06["__trial_b06__"] = _candidate_points_cm(candidate)
            selected_pa = None
            selected_pa_ports = None
            for pa_index, (pa_source, pa_side, pa_fraction) in enumerate(pa_variants):
                changed = copy.deepcopy(routes)
                changed["A-B-06"]["sourcePortFraction"] = source_fraction
                changed["A-B-06"]["targetSide"] = target_side
                changed["A-B-06"]["targetPortFraction"] = target_fraction
                changed["A-PA-07"]["sourcePortFraction"] = pa_source
                changed["A-PA-07"]["targetSide"] = pa_side
                changed["A-PA-07"]["targetPortFraction"] = pa_fraction
                if genus(changed, nodes) != 0:
                    continue
                px, py = build_axes(sem, [changed["A-PA-07"]], nodes, hard_b06)
                pix, piy, pallowed = build_graph(px, py, nodes, hard_b06)
                pa_generated = _candidate_pool(
                    changed["A-PA-07"], nodes, px, py, pix, piy, pallowed,
                    args.pair_samples + 2,
                    args.seed + tested * 100003 + candidate_index * 7919 + pa_index * 17,
                )
                for pa_candidate_index, pa_candidate in enumerate(pa_generated):
                    if candidates_contact(candidate, pa_candidate):
                        continue
                    try:
                        pa_candidate = make_candidate({
                            "routeId": "A-PA-07", "family": "b06-pa-conditioned",
                            "points": _candidate_points_cm(pa_candidate),
                            "cost": pa_candidate.cost + 0.25,
                            "tag": f"A-PA-07:b06:{args.shard_index}:{tested}:{candidate_index}:{pa_index}:{pa_candidate_index}",
                        })
                    except ValueError:
                        continue
                    if all(any(not candidates_contact(pa_candidate, other) for other in pools[rid])
                           for rid in CLUSTER[2:]):
                        selected_pa = pa_candidate
                        selected_pa_ports = {
                            "sourcePortFraction": pa_source,
                            "targetSide": pa_side,
                            "targetPortFraction": pa_fraction,
                        }
                        break
                if selected_pa is not None:
                    break
            if selected_pa is None:
                continue
            supported = True
            for rid in CLUSTER[2:]:
                if any(not candidates_contact(candidate, other) and not candidates_contact(selected_pa, other)
                       for other in pools[rid]):
                    continue
                hard = dict(hard_b06)
                hard["__trial_pa__"] = _candidate_points_cm(selected_pa)
                reroute = routes[rid]
                rx, ry = build_axes(sem, [reroute], nodes, hard)
                rix, riy, rallowed = build_graph(rx, ry, nodes, hard)
                repairs = _candidate_pool(
                    reroute, nodes, rx, ry, rix, riy, rallowed,
                    args.pair_samples,
                    args.seed + tested * 100003 + candidate_index * 7919
                    + sum(map(ord, rid)) * 101,
                )
                compatible = []
                for repair_index, repair in enumerate(repairs):
                    if candidates_contact(candidate, repair) or candidates_contact(selected_pa, repair):
                        continue
                    try:
                        retagged = make_candidate({
                            "routeId": rid, "family": "b06-pa-conditioned",
                            "points": _candidate_points_cm(repair),
                            "cost": repair.cost + 0.50,
                            "tag": f"{rid}:b06pa:{args.shard_index}:{tested}:{candidate_index}:{repair_index}",
                        })
                    except ValueError:
                        continue
                    compatible.append(retagged)
                if not compatible:
                    supported = False
                    break
                for repair in compatible:
                    _merge_candidate(pools[rid], repair)
            if not supported:
                continue
            _merge_candidate(pools["A-PA-07"], selected_pa)
            pa_ports[selected_pa.points] = selected_pa_ports
            before = len(b06_pool)
            _merge_candidate(b06_pool, candidate)
            if len(b06_pool) > before:
                b06_ports[candidate.points] = {
                    "sourcePortFraction": source_fraction,
                    "targetSide": target_side,
                    "targetPortFraction": target_fraction,
                }
        if len(b06_pool) >= args.max_b06_candidates:
            break
    pools = {"A-B-06": b06_pool, **pools}

    payload = {
        "status": "FAIL", "plan": PLAN, "shardIndex": args.shard_index,
        "testedPortVariants": tested, "elapsedSeconds": time.monotonic() - started,
        "candidateCounts": {rid: len(values) for rid, values in pools.items()},
        "fixedSeedRouteCount": len(witness_by_id),
    }
    if args.include_candidates:
        payload["candidatePools"] = {}
        for rid, values in pools.items():
            payload["candidatePools"][rid] = []
            for candidate in values:
                item = {
                    "points": _candidate_points_cm(candidate),
                    "cost": candidate.cost,
                    "family": candidate.family,
                    "tag": candidate.key,
                }
                if rid == "A-B-06" and candidate.points in b06_ports:
                    item["portOverrides"] = b06_ports[candidate.points]
                if rid == "A-PA-07" and candidate.points in pa_ports:
                    item["portOverrides"] = pa_ports[candidate.points]
                payload["candidatePools"][rid].append(item)
    if args.export_only:
        payload["status"] = "POOL"
        return payload
    if any(not values for values in pools.values()):
        payload["reason"] = "empty-route-domain"
        payload["emptyRoutes"] = [rid for rid, values in pools.items() if not values]
        return payload

    pair_repair = _repair_pairwise_gaps(
        pools=pools, routes=local_routes, nodes=nodes, xs=xs, ys=ys,
        frozen=frozen, rounds=args.pair_repair_rounds,
        synth_samples=args.pair_repair_samples,
        fixed_limit=args.pair_repair_fixed_limit,
        seed=args.seed + args.shard_index * 1000003,
    )
    payload["pairRepair"] = pair_repair
    conflicts = build_conflicts(pools)
    pair_rows = route_pair_compatibility(pools, conflicts=conflicts)
    impossible = [row for row in pair_rows if row["compatiblePairs"] == 0]
    payload["impossibleRoutePairs"] = impossible
    if impossible:
        payload["reason"] = "pairwise-impossible-current-pool"
        return payload
    ac3 = arc_consistency_prune(pools, conflicts=conflicts)
    arc_repair = []
    if ac3["status"] != "PASS":
        arc_repair = _repair_arc_empty_routes(
            pools=pools, routes=local_routes, nodes=nodes, xs=xs, ys=ys,
            frozen=frozen, rounds=args.arc_repair_rounds,
            synth_samples=args.arc_repair_samples,
            bundle_limit=args.arc_repair_bundle_limit,
            seed=args.seed + args.shard_index * 3000017,
        )
        conflicts = build_conflicts(pools)
        ac3 = arc_consistency_prune(pools, conflicts=conflicts)
    payload["arcRepair"] = arc_repair
    payload["arcConsistency"] = {
        "status": ac3["status"], "rounds": ac3["rounds"],
        "emptyRoutes": ac3["emptyRoutes"],
        "domainSizes": {rid: len(values) for rid, values in ac3["domains"].items()},
    }
    if ac3["status"] != "PASS":
        payload["reason"] = "arc-consistency-infeasible"
        return payload
    result = find_first_solution(ac3["domains"], conflicts=build_conflicts(ac3["domains"]),
                                 time_limit_seconds=max(10.0, args.seconds - (time.monotonic() - started)))
    payload["selector"] = {k: v for k, v in result.items() if k != "selection"}
    if result["status"] != "PASS":
        payload["reason"] = "selector-no-solution"
        return payload
    payload["status"] = "PASS"
    payload["selection"] = {}
    for rid, candidate in result["selection"].items():
        payload["selection"][rid] = {
            "points": [[x / 200.0, y / 200.0] for x, y in candidate.points],
            "family": candidate.family, "cost": candidate.cost,
        }
        if rid == "A-B-06":
            payload["selection"][rid]["portOverrides"] = b06_ports[candidate.points]
        if rid == "A-PA-07" and candidate.points in pa_ports:
            payload["selection"][rid]["portOverrides"] = pa_ports[candidate.points]
    return payload


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--fixed-routes", type=Path, required=True)
    parser.add_argument("--shard-index", type=int, required=True)
    parser.add_argument("--shard-count", type=int, default=8)
    parser.add_argument("--route-samples", type=int, default=48)
    parser.add_argument("--port-samples", type=int, default=6)
    parser.add_argument("--pair-samples", type=int, default=2)
    parser.add_argument("--pair-repair-rounds", type=int, default=3)
    parser.add_argument("--pair-repair-samples", type=int, default=4)
    parser.add_argument("--pair-repair-fixed-limit", type=int, default=8)
    parser.add_argument("--arc-repair-rounds", type=int, default=4)
    parser.add_argument("--arc-repair-samples", type=int, default=6)
    parser.add_argument("--arc-repair-bundle-limit", type=int, default=30)
    parser.add_argument("--independent-pa", action="store_true")
    parser.add_argument("--include-candidates", action="store_true")
    parser.add_argument("--export-only", action="store_true")
    parser.add_argument("--max-b06-candidates", type=int, default=180)
    parser.add_argument("--seconds", type=float, default=720.0)
    parser.add_argument("--seed", type=int, default=20260908)
    parser.add_argument("--json-out", type=Path, required=True)
    args = parser.parse_args()
    payload = run(args)
    args.json_out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if payload["status"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
