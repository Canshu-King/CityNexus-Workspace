"""Build a repair worklist from the hardened P1 route contact audit.

This script does not alter the route YAML. It turns the current contact audit
into a ranked, deterministic worklist for the 18 Association routes while
treating the three C4E1 Extend routes as frozen obstacles.
"""
from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "out"
CONTACT = OUT / "P1_UC_ROUTE_CONTACT-AUDIT.json"
CANDIDATE = HERE.parent / "phase1-routing-rc6-candidate.yaml"
REPORT = OUT / "P1_UC_ROUTE_REPAIR-WORKLIST.json"

FROZEN_EXTEND = {"EXT-07-06", "EXT-09-08", "EXT-10-09"}

# Human-reviewed routing hints. These are suggestions, not semantic constraints.
HINTS = {
    "A-T-UC-06": "Prefer UC-06 RIGHT; the frozen EXT-07-06 blocks clean LEFT access.",
    "A-T-UC-08": "Prefer UC-08 RIGHT and approach below the frozen EXT-09-08 envelope.",
    "A-CD-UC-10": "Prefer UC-10 TOP with a left-half port (x < 23.3).",
    "A-M-UC-10": "Prefer a distinct UC-10 TOP port on the left half.",
    "A-M-UC-08": "Prefer routing below EXT-10-09, then enter UC-08 from RIGHT.",
    "A-CE-09": "Prefer UC-09 LEFT; route below the lower obstacles before approaching.",
    "A-B-06": "Prefer entering the inner page above the EXT-10-09 top segment (y < 9.4).",
    "A-PA-07": "Prefer a separate lane above the EXT-10-09 top segment (y < 9.4).",
}

def main() -> int:
    contact = json.loads(CONTACT.read_text(encoding="utf-8"))

    degree = Counter()
    by_type = defaultdict(Counter)
    ext_contacts = Counter()
    adjacency = defaultdict(set)

    for item in contact["contacts"]:
        a = item["routeA"]
        b = item["routeB"]
        typ = item["type"]

        degree[a] += 1
        degree[b] += 1
        by_type[a][typ] += 1
        by_type[b][typ] += 1
        adjacency[a].add(b)
        adjacency[b].add(a)

        if a in FROZEN_EXTEND and b not in FROZEN_EXTEND:
            ext_contacts[b] += 1
        if b in FROZEN_EXTEND and a not in FROZEN_EXTEND:
            ext_contacts[a] += 1

    short = Counter(item["route"] for item in contact["shortSegments"])
    redundant = Counter(item["route"] for item in contact["redundantCollinearPoints"])

    routes = sorted(
        route
        for route in set(degree) | set(short) | set(redundant)
        if route not in FROZEN_EXTEND
    )

    rows = []
    for route in routes:
        # Frozen-Extend contacts are the most urgent because those three routes
        # are not available for rip-up. Then rank by total contacts and route
        # representation quality.
        score = (
            100 * ext_contacts[route]
            + 10 * degree[route]
            + 3 * short[route]
            + redundant[route]
        )
        rows.append({
            "route": route,
            "priorityScore": score,
            "totalContacts": degree[route],
            "frozenExtendContacts": ext_contacts[route],
            "contactTypes": dict(by_type[route]),
            "shortSegments": short[route],
            "redundantCollinearPoints": redundant[route],
            "conflictsWith": sorted(adjacency[route]),
            "hint": HINTS.get(route),
        })

    rows.sort(key=lambda row: (-row["priorityScore"], row["route"]))

    payload = {
        "status": "REPAIR_REQUIRED" if contact["status"] != "PASS" else "CLEAN",
        "frozenExtendRoutes": sorted(FROZEN_EXTEND),
        "associationRepairCount": len(rows),
        "repairOrder": [row["route"] for row in rows],
        "routes": rows,
        "global": {
            "contactPairCount": contact["contactPairCount"],
            "uniqueContactCount": contact["uniqueContactCount"],
            "contactCounts": contact["contactCounts"],
            "shortSegmentCount": contact["shortSegmentCount"],
            "redundantCollinearPointCount": contact["redundantCollinearPointCount"],
        },
        "strategy": [
            "Do not repair contacts one-by-one with micro-jogs.",
            "Rip up and coherently re-plan Association routes, highest-priority first.",
            "Treat all three Extend polylines as frozen obstacles.",
            "Use distinct orthogonal lanes and distinct intermediate waypoints.",
            "Re-run validate_p1_route_candidate_v3.py after each coherent batch.",
        ],
    }

    REPORT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=True, indent=2))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
