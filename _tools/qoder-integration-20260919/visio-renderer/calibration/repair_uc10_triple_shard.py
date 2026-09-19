#!/usr/bin/env python3
"""Repair the missing B06/CD10/M10 three-route compatibility bundle."""
from __future__ import annotations

import argparse
import copy
import glob
import json
import sys
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent), str(HERE)]

from explore_p1_disjoint_pool import _candidate_points_cm, _candidate_pool
from route_candidate_selector import candidates_contact, make_candidate
from route_p1_negotiated_grid import build_axes, build_graph, load
from routing_geometry import route_points

PLAN = "PLAN_QUOTA_SAVER_DUAL_ROTATED_20260908"


def collect(pattern, route_ids):
    raw = {rid: [] for rid in route_ids}
    seen = {rid: set() for rid in route_ids}
    for filename in sorted(glob.glob(pattern)):
        data = json.load(open(filename, encoding="utf-8"))
        for rid in route_ids:
            for item in data.get("candidatePools", {}).get(rid, []):
                key = tuple(tuple(point) for point in item["points"])
                if key in seen[rid]:
                    continue
                seen[rid].add(key)
                raw[rid].append(item)
    return raw


def candidate(rid, raw, index):
    return make_candidate({
        "routeId": rid, "family": "triple-source", "points": raw["points"],
        "cost": raw.get("cost", 0.0), "tag": f"{rid}:triple:{index}",
    })


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-pattern", required=True)
    parser.add_argument("--fixed-routes", type=Path, required=True)
    parser.add_argument("--reroute", choices=("A-CD-UC-10", "A-M-UC-10"), required=True)
    parser.add_argument("--shard-index", type=int, required=True)
    parser.add_argument("--shard-count", type=int, default=6)
    parser.add_argument("--pair-limit", type=int, default=120)
    parser.add_argument("--samples", type=int, default=12)
    parser.add_argument("--seed", type=int, default=20260908)
    parser.add_argument("--json-out", type=Path, required=True)
    args = parser.parse_args()

    if args.reroute == "A-M-UC-10":
        fixed_ids = ("A-B-06", "A-CD-UC-10")
    else:
        fixed_ids = ("A-B-06", "A-M-UC-10")
    all_ids = (*fixed_ids, args.reroute)

    sem, _original, nodes, routes, _overrides, frozen, _mutable = load(PLAN)
    witness = yaml.safe_load(args.fixed_routes.read_text(encoding="utf-8")) or {}
    for item in witness.get("routes", []):
        supplied = copy.deepcopy(routes[item["id"]])
        supplied.update({key: copy.deepcopy(value) for key, value in item.items() if key != "id"})
        frozen[f"seed:{item['id']}"] = route_points(supplied, nodes)

    raw = collect(args.input_pattern, all_ids)
    first = [(candidate(fixed_ids[0], item, index), item) for index, item in enumerate(raw[fixed_ids[0]])]
    second = [(candidate(fixed_ids[1], item, index), item) for index, item in enumerate(raw[fixed_ids[1]])]
    pairs = []
    for a, a_raw in first:
        for b, b_raw in second:
            if candidates_contact(a, b):
                continue
            pairs.append((a.cost + b.cost, a, a_raw, b, b_raw))
    pairs.sort(key=lambda item: (item[0], item[1].points, item[3].points))
    pairs = pairs[:args.pair_limit][args.shard_index::args.shard_count]

    exported = {rid: [] for rid in all_ids}
    reroute = routes[args.reroute]
    for pair_index, (_cost, a, a_raw, b, b_raw) in enumerate(pairs):
        hard = dict(frozen)
        hard[f"__{fixed_ids[0]}__"] = _candidate_points_cm(a)
        hard[f"__{fixed_ids[1]}__"] = _candidate_points_cm(b)
        rx, ry = build_axes(sem, [reroute], nodes, hard)
        rix, riy, allowed = build_graph(rx, ry, nodes, hard)
        generated = _candidate_pool(
            reroute, nodes, rx, ry, rix, riy, allowed, args.samples,
            args.seed + args.shard_index * 1000003 + pair_index * 50021,
        )
        legal = [item for item in generated if not candidates_contact(item, a) and not candidates_contact(item, b)]
        if not legal:
            continue
        exported[fixed_ids[0]].append(a_raw)
        exported[fixed_ids[1]].append(b_raw)
        for item in legal:
            exported[args.reroute].append({
                "points": _candidate_points_cm(item), "cost": item.cost,
                "family": "uc10-triple-conditioned",
            })

    payload = {
        "status": "POOL", "reroute": args.reroute,
        "shardIndex": args.shard_index, "compatiblePairCount": len(pairs),
        "candidatePools": exported,
        "candidateCounts": {rid: len(values) for rid, values in exported.items()},
    }
    args.json_out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
