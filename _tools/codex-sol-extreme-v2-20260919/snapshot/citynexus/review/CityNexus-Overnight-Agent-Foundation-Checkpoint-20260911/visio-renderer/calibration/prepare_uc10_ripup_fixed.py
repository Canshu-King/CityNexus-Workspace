#!/usr/bin/env python3
"""Extract a conflict witness while leaving the UC-10 triple mutable."""
import argparse
import copy
from pathlib import Path
import yaml

DEFAULT_RIPUP = {"A-B-06", "A-CD-UC-10", "A-M-UC-10", "A-M-UC-08", "A-PA-07"}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--witness", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--ripup", action="append", default=[])
    args = ap.parse_args()
    doc = yaml.safe_load(args.witness.read_text(encoding="utf-8")) or {}
    ripup = set(args.ripup) if args.ripup else DEFAULT_RIPUP
    routes = [copy.deepcopy(r) for r in doc.get("routes", []) if r.get("id") not in ripup]
    payload = {"metadata": {"status": "RIPUP_FIXED_WITNESS", "mutableConflictCluster": sorted(ripup)}, "routes": routes}
    args.out.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")
    print({"fixedCount": len(routes), "mutable": sorted(ripup)})

if __name__ == "__main__":
    main()
