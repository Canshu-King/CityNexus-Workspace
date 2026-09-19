#!/usr/bin/env python3
"""Prepare the 14-route fixed seed and four-route port overrides from a near witness."""
from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path

import yaml

FIXED_NEAR = {"A-CE-09", "A-M-UC-08", "A-CD-UC-04", "A-M-UC-04"}
MUTABLE_FOUR = {"A-B-06", "A-PA-07", "A-CD-UC-10", "A-M-UC-10"}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--near", type=Path, required=True)
    parser.add_argument("--seed", type=Path, required=True)
    parser.add_argument("--fixed-out", type=Path, required=True)
    parser.add_argument("--overrides-out", type=Path, required=True)
    args = parser.parse_args()

    near = json.loads(args.near.read_text(encoding="utf-8"))
    seed = yaml.safe_load(args.seed.read_text(encoding="utf-8")) or {}
    fixed_routes = copy.deepcopy(seed.get("routes", []))
    for rid in sorted(FIXED_NEAR):
        raw = near["routes"][rid]
        fixed_routes.append({
            "id": rid,
            "sourcePortFraction": raw["sourcePortFraction"],
            "targetSide": raw["targetSide"],
            "targetPortFraction": raw["targetPortFraction"],
            "waypoints": raw["points"][1:-1],
        })
    fixed = {
        "metadata": {"status": "NEAR_WITNESS_TEMPORARY", "associationCount": len(fixed_routes)},
        "routes": fixed_routes,
    }
    overrides = {
        "routes": {
            rid: {
                key: near["routes"][rid][key]
                for key in ("sourcePortFraction", "targetSide", "targetPortFraction")
            }
            for rid in sorted(MUTABLE_FOUR)
        }
    }
    args.fixed_out.write_text(yaml.safe_dump(fixed, sort_keys=False), encoding="utf-8")
    args.overrides_out.write_text(yaml.safe_dump(overrides, sort_keys=False), encoding="utf-8")
    print(json.dumps({"fixedCount": len(fixed_routes), "mutableCount": len(overrides["routes"])}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
