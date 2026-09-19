#!/usr/bin/env python3
"""Minimal executable counterexample for CX-SOL-001."""
from __future__ import annotations

import json

PLAN = {
    "current_activity_id": "act-2",
    "activities": [
        {"id": "act-1", "title": "Completed museum"},
        {"id": "act-2", "title": "Current lunch"},
        {"id": "act-3", "title": "Next ferry"},
    ],
    "legs": [
        {"id": "leg-1", "mode": "WALK"},
        {"id": "leg-2", "mode": "TRANSIT"},
    ],
}


def baseline_projection(plan: dict) -> dict:
    return {"now": plan["activities"][0], "next": plan["activities"][1], "leg": plan["legs"][0]}


def candidate_projection(plan: dict) -> dict:
    index = next((i for i, item in enumerate(plan["activities"]) if item["id"] == plan["current_activity_id"]), 0)
    return {
        "now": plan["activities"][index],
        "next": plan["activities"][index + 1] if index + 1 < len(plan["activities"]) else None,
        "leg": plan["legs"][index] if index < len(plan["legs"]) else None,
    }


old = baseline_projection(PLAN)
new = candidate_projection(PLAN)
assert old["now"]["id"] != PLAN["current_activity_id"]
assert new["now"]["id"] == PLAN["current_activity_id"]
assert new["next"]["id"] == "act-3"
assert new["leg"]["id"] == "leg-2"
print(json.dumps({"finding": "CX-SOL-001", "baseline": old, "candidate": new}, indent=2))
