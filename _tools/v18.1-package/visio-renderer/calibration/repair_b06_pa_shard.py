#!/usr/bin/env python3
"""Generate PA07 port/corridor candidates around the 18 strong B06 routes."""
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


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-pattern", required=True)
    parser.add_argument("--fixed-routes", type=Path, required=True)
    parser.add_argument("--shard-index", type=int, required=True)
    parser.add_argument("--shard-count", type=int, default=12)
    parser.add_argument("--samples", type=int, default=6)
    parser.add_argument("--seed", type=int, default=20260908)
    parser.add_argument("--json-out", type=Path, required=True)
    args = parser.parse_args()

    sem, _original, nodes, routes, _overrides, frozen, _mutable = load(PLAN)
    witness = yaml.safe_load(args.fixed_routes.read_text(encoding="utf-8")) or {}
    for raw in witness.get("routes", []):
        supplied = copy.deepcopy(routes[raw["id"]])
        supplied.update({key: copy.deepcopy(value) for key, value in raw.items() if key != "id"})
        frozen[f"seed:{raw['id']}"] = route_points(supplied, nodes)

    raw_b06 = []
    seen = set()
    for filename in sorted(glob.glob(args.input_pattern)):
        data = json.load(open(filename, encoding="utf-8"))
        for raw in data.get("candidatePools", {}).get("A-B-06", []):
            key = tuple(tuple(point) for point in raw["points"])
            if key not in seen:
                seen.add(key)
                raw_b06.append(raw)
    raw_b06 = raw_b06[args.shard_index::args.shard_count]

    pa = routes["A-PA-07"]
    pa_targets = []
    for side in ("RIGHT", "TOP", "BOTTOM", "LEFT"):
        options = [item for item in target_options(nodes[pa["target"]]) if item[0] == side]
        for wanted in (0.10, 0.25, 0.50, 0.75, 0.90):
            value = min(options, key=lambda item: abs(float(item[1]) - wanted))
            if value not in pa_targets:
                pa_targets.append(value)
    pa_sources_all = exact_source_fractions(nodes[pa["source"]])
    pa_sources = []
    for wanted in (0.10, 0.25, 0.50, 0.75, 0.90):
        value = min(pa_sources_all, key=lambda item: abs(item - wanted))
        if value not in pa_sources:
            pa_sources.append(value)

    exported_b06 = []
    exported_pa = []
    for b_index, raw in enumerate(raw_b06):
        b_candidate = make_candidate({
            "routeId": "A-B-06", "family": "strong-b06",
            "points": raw["points"], "cost": raw.get("cost", 0.0),
            "tag": f"B06:{args.shard_index}:{b_index}",
        })
        b_ports = raw["portOverrides"]
        hard = dict(frozen)
        hard["__strong_b06__"] = _candidate_points_cm(b_candidate)
        found_for_b06 = 0
        for pa_source in pa_sources:
            for pa_side, pa_fraction in pa_targets:
                changed = copy.deepcopy(routes)
                changed["A-B-06"].update(b_ports)
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
                    args.seed + args.shard_index * 1000003 + b_index * 50021
                    + int(pa_source * 1000) + int(pa_fraction * 100),
                )
                for candidate in generated:
                    if candidates_contact(b_candidate, candidate):
                        continue
                    exported_pa.append({
                        "points": _candidate_points_cm(candidate),
                        "cost": candidate.cost, "family": "pa-around-b06",
                        "portOverrides": {
                            "sourcePortFraction": pa_source,
                            "targetSide": pa_side,
                            "targetPortFraction": pa_fraction,
                        },
                    })
                    found_for_b06 += 1
                if found_for_b06 >= 30:
                    break
            if found_for_b06 >= 30:
                break
        if found_for_b06:
            exported_b06.append(raw)

    payload = {
        "status": "POOL", "shardIndex": args.shard_index,
        "strongB06InputCount": len(raw_b06),
        "candidatePools": {"A-B-06": exported_b06, "A-PA-07": exported_pa},
        "candidateCounts": {"A-B-06": len(exported_b06), "A-PA-07": len(exported_pa)},
    }
    args.json_out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
