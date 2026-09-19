#!/usr/bin/env python3
"""Generate PA07 candidates around compatible B06/CD10/M10 blocker bundles."""
from __future__ import annotations

import argparse
import copy
import glob
import json
import math
import sys
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent), str(HERE)]

from explore_p1_disjoint_pool import _candidate_points_cm, _candidate_pool
from route_candidate_selector import candidates_contact, make_candidate
from route_p1_negotiated_grid import build_axes, build_graph, load
from routing_geometry import route_points
from search_p1_global_port_rotations import genus, target_options

PLAN = "PLAN_QUOTA_SAVER_DUAL_ROTATED_20260908"
BLOCKERS = ("A-B-06", "A-CD-UC-10", "A-M-UC-10")


def source_values(node):
    top = float(node["y"]) - float(node["height"]) / 2.0
    height = float(node["height"])
    first = math.ceil((top + 0.05) * 10.0) / 10.0
    last = math.floor((top + height - 0.05) * 10.0) / 10.0
    all_values = []
    y = first
    while y <= last + 1e-9:
        all_values.append((y - top) / height)
        y = round(y + 0.1, 10)
    values = []
    for wanted in (0.25, 0.50, 0.75):
        value = min(all_values, key=lambda item: abs(item - wanted))
        if value not in values:
            values.append(value)
    return values


def collect(pattern, reach_evidence=None):
    raw = {rid: [] for rid in BLOCKERS}
    seen = {rid: set() for rid in BLOCKERS}
    for filename in sorted(glob.glob(pattern)):
        data = json.load(open(filename, encoding="utf-8"))
        for rid in BLOCKERS:
            for item in data.get("candidatePools", {}).get(rid, []):
                key = tuple(tuple(point) for point in item["points"])
                if key in seen[rid]:
                    continue
                seen[rid].add(key)
                raw[rid].append(item)
    if reach_evidence is not None:
        evidence = json.loads(reach_evidence.read_text(encoding="utf-8"))
        for row in evidence:
            for rid, points in row.get("reach", {}).items():
                if rid not in raw or not points:
                    continue
                key = tuple(tuple(point) for point in points)
                if key in seen[rid]:
                    continue
                seen[rid].add(key)
                raw[rid].append({
                    "points": points,
                    "cost": 0.0,
                    "family": f"upper-reachability-{row['index']}",
                })
    return raw


def as_candidate(rid, raw, index):
    return make_candidate({
        "routeId": rid, "family": "bundle-source", "points": raw["points"],
        "cost": raw.get("cost", 0.0), "tag": f"{rid}:bundle:{index}",
    })


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-pattern", required=True)
    parser.add_argument("--fixed-routes", type=Path, required=True)
    parser.add_argument("--reach-evidence", type=Path)
    parser.add_argument("--shard-index", type=int, required=True)
    parser.add_argument("--shard-count", type=int, default=12)
    parser.add_argument("--bundle-limit", type=int, default=60)
    parser.add_argument("--samples", type=int, default=4)
    parser.add_argument("--seed", type=int, default=20260908)
    parser.add_argument("--json-out", type=Path, required=True)
    args = parser.parse_args()

    sem, _original, nodes, routes, _overrides, frozen, _mutable = load(PLAN)
    witness = yaml.safe_load(args.fixed_routes.read_text(encoding="utf-8")) or {}
    for item in witness.get("routes", []):
        supplied = copy.deepcopy(routes[item["id"]])
        supplied.update({key: copy.deepcopy(value) for key, value in item.items() if key != "id"})
        frozen[f"seed:{item['id']}"] = route_points(supplied, nodes)

    raw = collect(args.input_pattern, args.reach_evidence)
    candidates = {
        rid: [(as_candidate(rid, item, index), item) for index, item in enumerate(values)]
        for rid, values in raw.items()
    }
    bundles = []
    for b, b_raw in candidates["A-B-06"]:
        for cd, cd_raw in candidates["A-CD-UC-10"]:
            if candidates_contact(b, cd):
                continue
            for m, m_raw in candidates["A-M-UC-10"]:
                if candidates_contact(b, m) or candidates_contact(cd, m):
                    continue
                bundles.append((b.cost + cd.cost + m.cost, b, b_raw, cd, cd_raw, m, m_raw))
    bundles.sort(key=lambda item: (item[0], item[1].points, item[3].points, item[5].points))
    bundles = bundles[:args.bundle_limit][args.shard_index::args.shard_count]

    pa = routes["A-PA-07"]
    pa_targets = []
    for side in ("RIGHT", "TOP", "BOTTOM", "LEFT"):
        options = [item for item in target_options(nodes[pa["target"]]) if item[0] == side]
        for wanted in (0.25, 0.50, 0.75):
            value = min(options, key=lambda item: abs(float(item[1]) - wanted))
            if value not in pa_targets:
                pa_targets.append(value)

    exported = {rid: [] for rid in (*BLOCKERS, "A-PA-07")}
    for bundle_index, (_cost, b, b_raw, cd, cd_raw, m, m_raw) in enumerate(bundles):
        hard = dict(frozen)
        hard["__b06__"] = _candidate_points_cm(b)
        hard["__cd10__"] = _candidate_points_cm(cd)
        hard["__m10__"] = _candidate_points_cm(m)
        found = 0
        for pa_source in source_values(nodes[pa["source"]]):
            for pa_side, pa_fraction in pa_targets:
                changed = copy.deepcopy(routes)
                changed["A-B-06"].update(b_raw.get("portOverrides") or {})
                changed["A-PA-07"]["sourcePortFraction"] = pa_source
                changed["A-PA-07"]["targetSide"] = pa_side
                changed["A-PA-07"]["targetPortFraction"] = pa_fraction
                if genus(changed, nodes) != 0:
                    continue
                px, py = build_axes(sem, [changed["A-PA-07"]], nodes, hard)
                pix, piy, allowed = build_graph(px, py, nodes, hard)
                generated = _candidate_pool(
                    changed["A-PA-07"], nodes, px, py, pix, piy, allowed,
                    args.samples,
                    args.seed + args.shard_index * 1000003 + bundle_index * 50021
                    + int(pa_source * 1000) + int(pa_fraction * 100),
                )
                for candidate in generated:
                    if any(candidates_contact(candidate, blocker) for blocker in (b, cd, m)):
                        continue
                    exported["A-PA-07"].append({
                        "points": _candidate_points_cm(candidate), "cost": candidate.cost,
                        "family": "pa-bundle-conditioned",
                        "portOverrides": {
                            "sourcePortFraction": pa_source,
                            "targetSide": pa_side,
                            "targetPortFraction": pa_fraction,
                        },
                    })
                    found += 1
                if found >= 24:
                    break
            if found >= 24:
                break
        if found:
            exported["A-B-06"].append(b_raw)
            exported["A-CD-UC-10"].append(cd_raw)
            exported["A-M-UC-10"].append(m_raw)

    payload = {
        "status": "POOL", "shardIndex": args.shard_index,
        "bundleCount": len(bundles),
        "candidatePools": exported,
        "candidateCounts": {rid: len(values) for rid, values in exported.items()},
    }
    args.json_out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
