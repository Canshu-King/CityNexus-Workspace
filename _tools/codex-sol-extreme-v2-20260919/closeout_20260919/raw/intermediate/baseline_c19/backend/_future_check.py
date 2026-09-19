"""Check whether build_resilience_snapshot counts already-completed activities."""

from __future__ import annotations

from fastapi.testclient import TestClient

import app.main as main_module
from app.agent import predictive
from app.db.models import Activity, Journey
from app.db.session import SessionLocal

client = TestClient(main_module.app)

ids = client.post("/api/v1/demo/reset").json()
journey_id = ids["journey_id"]

generated = client.post(
    f"/api/v1/journeys/{journey_id}/plans/generate", json={"candidate_count": 1}
).json()
plan = generated[0]
client.post(f"/api/v1/journeys/{journey_id}/plans/{plan['id']}/select")
client.post(f"/api/v1/journeys/{journey_id}/start")

with SessionLocal() as session:
    journey = session.get(Journey, journey_id)
    activities = predictive._active_activities(session, journey)
    outdoor = next(
        item
        for item in activities
        if "place-tech-art" == item.place_id or "place-old-town" == item.place_id
    )
    target_id = outdoor.id
    target_title = outdoor.title

print(f"target activity: {target_title} ({target_id})")

# Complete it the way a traveler would, through the public API.
completed = client.post(
    f"/api/v1/journeys/{journey_id}/activities/{target_id}/complete"
)
print("complete ->", completed.status_code)

with SessionLocal() as session:
    journey = session.get(Journey, journey_id)
    rows = predictive._active_activities(session, journey)
    statuses = {row.id: row.status for row in rows}
    print("activity statuses:", statuses)

    future_ids = [row.id for row in rows if predictive._future(row, journey)]
    print("journey.start_at     :", journey.start_at)
    print("counted as 'future'  :", len(future_ids), "of", len(rows))
    print("completed still counted:", target_id in future_ids)

    snapshot = predictive.build_resilience_snapshot(session, journey)
    payload = predictive.snapshot_payload(snapshot) or {}
    risks = payload.get("components", {}).get("activity_risks") or payload.get("activity_risks")
    print("snapshot status      :", payload.get("status"))
    print("activity_risks count :", len(risks) if isinstance(risks, list) else risks)
    if isinstance(risks, list):
        for item in risks:
            print("   -", item.get("activity_id"), item.get("risk"), item.get("modes"))

    activity_row = session.get(Activity, target_id)
    print("completed activity status in DB:", activity_row.status)
