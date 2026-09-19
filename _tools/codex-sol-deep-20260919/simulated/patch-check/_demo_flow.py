"""Drive the CityNexus flagship flow over the local API and print a summary.

Prerequisites (run from the repository root):
    .venv/Scripts/python.exe scripts/seed_demo.py      # clean fixture, run with cwd=backend
    .venv/Scripts/python.exe -m uvicorn app.main:app   # from backend/, port 8000

Then:
    .venv/Scripts/python.exe _demo_flow.py

Flow: generate plan -> select -> start journey -> inspect twin -> inject a CLOSURE
event -> generate a replan proposal -> accept it -> show the mutated active plan.
"""

from __future__ import annotations

import json
import sys
import time

import httpx

BASE = "http://127.0.0.1:8000/api/v1"
JOURNEY = "22222222-2222-4222-8222-222222222222"

client = httpx.Client(base_url=BASE, timeout=180.0)


def show(label: str, payload: object) -> None:
    print(f"\n--- {label} ---")
    print(json.dumps(payload, ensure_ascii=False, sort_keys=True, default=str)[:800])


def plans() -> list[dict]:
    data = client.get(f"/journeys/{JOURNEY}/plans").json()
    return data if isinstance(data, list) else data.get("items", [])


journey = client.get(f"/journeys/{JOURNEY}").json()
show("1. journey before", {"status": journey["status"], "active_plan": journey["active_plan_version_id"]})

generated = client.post(f"/journeys/{JOURNEY}/plans/generate", json={}).json()
plan_id = generated[0]["id"]
show(
    "2. generated plan",
    {
        "plan_id": plan_id,
        "utility_score": generated[0]["utility_score"],
        "total_cost_minor": generated[0]["total_cost"]["amount_minor"],
        "titles": [a["title"] for a in generated[0]["activities"]],
    },
)

client.post(f"/journeys/{JOURNEY}/plans/{plan_id}/select")
client.post(f"/journeys/{JOURNEY}/start")
twin = client.get(f"/journeys/{JOURNEY}/twin").json()
show("3. started + twin envelope", {"projection_status": twin.get("projection_status"), "context": twin.get("context")})

active = next((p for p in plans() if p.get("status") == "ACTIVE"), None)
target = next(
    (a for a in (active or {}).get("activities", []) if a.get("status") == "PLANNED" and not a.get("locked")),
    None,
)
if target is None:
    print("\n(no mutable planned activity; nothing left to disrupt)")
    sys.exit(0)

event = client.post(
    f"/journeys/{JOURNEY}/events",
    json={
        "event_type": "CLOSURE",
        "severity": "MAJOR",
        "affected_activity_id": target["id"],
        "provenance": "SIMULATED",
        "payload": {"reason": "demo closure"},
    },
).json()
show("4. event injected", {"event_id": event["id"], "type": event["event_type"], "target": target["title"]})

proposal = client.post(
    f"/journeys/{JOURNEY}/replans",
    json={"trigger_event_id": event["id"], "candidate_count": 3, "solver_mode": "v2"},
).json()
diff = proposal.get("diff", {})
show(
    "5. replan proposal (CP-SAT v2)",
    {
        "status": proposal.get("status"),
        "utility_score": proposal.get("utility_score"),
        "hard_constraints_passed": proposal.get("hard_constraints_passed"),
        "candidate_family": diff.get("candidate_family"),
        "removed": diff.get("removed"),
        "preserved_protected": diff.get("preserved_protected"),
        "cost_delta_minor": diff.get("cost_delta_minor"),
    },
)

accepted = client.post(
    f"/replans/{proposal['id']}/accept",
    json={},
    headers={"Idempotency-Key": f"demo-accept-{int(time.time())}"},
).json()
show("6. accepted", {"active_plan_version_id": accepted["journey"]["active_plan_version_id"]})

final = next((p for p in plans() if p.get("status") == "ACTIVE"), None)
print("\n--- 7. active plan after replan ---")
for activity in (final or {}).get("activities", []):
    print(f"   {activity['sequence_no']}. {activity['title']}  {activity['start_at']}")
