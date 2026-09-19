#!/usr/bin/env python3
"""Merge parallel quota-saver candidate shards and solve the exact route CSP."""
from __future__ import annotations

import argparse
import glob
import json
from pathlib import Path

from route_candidate_selector import (
    arc_consistency_prune, build_conflicts, find_first_solution, make_candidate,
    route_pair_compatibility,
)


def port_signature(raw):
    override = raw.get("portOverrides") or {}
    return tuple(sorted((key, str(value)) for key, value in override.items()))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--pattern", required=True)
    parser.add_argument("--limit", type=int, default=180)
    parser.add_argument("--seconds", type=float, default=300.0)
    parser.add_argument("--json-out", type=Path, required=True)
    args = parser.parse_args()

    raw_pools = {}
    files = sorted(glob.glob(args.pattern))
    for filename in files:
        data = json.load(open(filename, encoding="utf-8"))
        for rid, values in data.get("candidatePools", {}).items():
            raw_pools.setdefault(rid, []).extend(values)

    pools = {}
    overrides = {}
    source_counts = {}
    for rid, values in raw_pools.items():
        source_counts[rid] = len(values)
        unique = {}
        for raw in values:
            try:
                candidate = make_candidate({
                    "routeId": rid, "family": raw.get("family", "union"),
                    "points": raw["points"], "cost": raw.get("cost", 0.0),
                })
            except ValueError:
                continue
            key = (candidate.points, port_signature(raw))
            old = unique.get(key)
            if old is None or candidate.cost < old[0].cost:
                unique[key] = (candidate, raw.get("portOverrides"))

        rows = sorted(unique.values(), key=lambda item: (item[0].cost, item[0].points))
        chosen = []
        if rid in {"A-B-06", "A-PA-07"}:
            seen_ports = set()
            for candidate, override in rows:
                signature = tuple(sorted((override or {}).items()))
                if signature in seen_ports:
                    continue
                seen_ports.add(signature)
                chosen.append((candidate, override))
                if len(chosen) >= args.limit // 2:
                    break
            chosen_keys = {(candidate.points, tuple(sorted((override or {}).items()))) for candidate, override in chosen}
            for candidate, override in rows:
                key = (candidate.points, tuple(sorted((override or {}).items())))
                if key in chosen_keys:
                    continue
                chosen.append((candidate, override))
                if len(chosen) >= args.limit:
                    break
        else:
            chosen = rows[:args.limit]

        pools[rid] = []
        for index, (candidate, override) in enumerate(chosen):
            retagged = make_candidate({
                "routeId": rid, "family": candidate.family,
                "points": [[x / 200.0, y / 200.0] for x, y in candidate.points],
                "cost": candidate.cost, "tag": f"{rid}:union:{index}",
            })
            pools[rid].append(retagged)
            if override:
                overrides[retagged.key] = override

    payload = {
        "status": "FAIL", "shardFiles": files, "sourceCounts": source_counts,
        "selectedPoolCounts": {rid: len(values) for rid, values in pools.items()},
    }
    empty = [rid for rid, values in pools.items() if not values]
    if len(pools) != 6 or empty:
        payload["reason"] = "missing-or-empty-pools"
        payload["emptyRoutes"] = empty
    else:
        conflicts = build_conflicts(pools)
        pairs = route_pair_compatibility(pools, conflicts=conflicts)
        payload["impossibleRoutePairs"] = [row for row in pairs if row["compatiblePairs"] == 0]
        ac3 = arc_consistency_prune(pools, conflicts=conflicts)
        payload["arcConsistency"] = {
            "status": ac3["status"], "rounds": ac3["rounds"],
            "emptyRoutes": ac3["emptyRoutes"],
            "domainSizes": {rid: len(values) for rid, values in ac3["domains"].items()},
            "removalCount": len(ac3["removals"]),
            "removalBlockerCounts": {
                rid: {
                    blocker: sum(
                        blocker in row["unsupportedBy"]
                        for row in ac3["removals"] if row["route"] == rid
                    )
                    for blocker in pools if blocker != rid
                }
                for rid in pools
            },
        }
        if not payload["impossibleRoutePairs"] and ac3["status"] == "PASS":
            result = find_first_solution(
                ac3["domains"], conflicts=build_conflicts(ac3["domains"]),
                time_limit_seconds=args.seconds,
            )
            payload["selector"] = {key: value for key, value in result.items() if key != "selection"}
            if result["status"] == "PASS":
                payload["status"] = "PASS"
                payload["selection"] = {}
                for rid, candidate in result["selection"].items():
                    item = {
                        "points": [[x / 200.0, y / 200.0] for x, y in candidate.points],
                        "family": candidate.family, "cost": candidate.cost,
                    }
                    if candidate.key in overrides:
                        item["portOverrides"] = overrides[candidate.key]
                    payload["selection"][rid] = item
            else:
                payload["reason"] = "selector-no-solution"
        elif payload["impossibleRoutePairs"]:
            payload["reason"] = "pairwise-impossible-union"
        else:
            payload["reason"] = "arc-consistency-infeasible-union"

    args.json_out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if payload["status"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
