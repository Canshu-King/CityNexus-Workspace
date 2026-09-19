#!/usr/bin/env python3
"""Merge four-route candidate shards and select one exact contact-free route per ID."""
from __future__ import annotations

import argparse
import glob
import json
from pathlib import Path

from route_candidate_selector import (
    arc_consistency_prune, build_conflicts, find_first_solution, make_candidate,
    route_pair_compatibility,
)

CLUSTER = ("A-B-06", "A-PA-07", "A-CD-UC-10", "A-M-UC-10")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--pattern", required=True)
    parser.add_argument("--seconds", type=float, default=120.0)
    parser.add_argument("--json-out", type=Path, required=True)
    args = parser.parse_args()
    raw = {rid: [] for rid in CLUSTER}
    seen = {rid: set() for rid in CLUSTER}
    for filename in sorted(glob.glob(args.pattern)):
        data = json.load(open(filename, encoding="utf-8"))
        for rid in CLUSTER:
            for item in data.get("candidatePools", {}).get(rid, []):
                key = tuple(tuple(point) for point in item["points"])
                if key in seen[rid]:
                    continue
                seen[rid].add(key)
                raw[rid].append(item)
    pools = {}
    for rid, values in raw.items():
        pools[rid] = [
            make_candidate({
                "routeId": rid, "family": item.get("family", "four-union"),
                "points": item["points"], "cost": item.get("cost", 0.0),
                "tag": f"{rid}:four:{index}",
            })
            for index, item in enumerate(values)
        ]
    payload = {"status": "FAIL", "candidateCounts": {rid: len(v) for rid, v in pools.items()}}
    if any(not values for values in pools.values()):
        payload["reason"] = "empty-domain"
    else:
        conflicts = build_conflicts(pools)
        payload["impossiblePairs"] = [
            row for row in route_pair_compatibility(pools, conflicts=conflicts)
            if row["compatiblePairs"] == 0
        ]
        ac3 = arc_consistency_prune(pools, conflicts=conflicts)
        payload["arcConsistency"] = {
            "status": ac3["status"], "emptyRoutes": ac3["emptyRoutes"],
            "domainSizes": {rid: len(v) for rid, v in ac3["domains"].items()},
        }
        if not payload["impossiblePairs"] and ac3["status"] == "PASS":
            result = find_first_solution(
                ac3["domains"], conflicts=build_conflicts(ac3["domains"]),
                time_limit_seconds=args.seconds,
            )
            payload["selector"] = {key: value for key, value in result.items() if key != "selection"}
            if result["status"] == "PASS":
                payload["status"] = "PASS"
                payload["selection"] = {
                    rid: {
                        "points": [[x / 200.0, y / 200.0] for x, y in candidate.points],
                        "cost": candidate.cost, "family": candidate.family,
                    }
                    for rid, candidate in result["selection"].items()
                }
            else:
                payload["reason"] = "selector-failed"
        elif payload.get("impossiblePairs"):
            payload["reason"] = "pairwise-impossible"
        else:
            payload["reason"] = "arc-infeasible"
    args.json_out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if payload["status"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
