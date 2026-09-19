#!/usr/bin/env python3
"""Real API/SQLite race schedules for recovery and booking authority."""
from __future__ import annotations

import argparse
import json
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.db.models import Activity, Commitment, Event, Journey, PlanVersion, ReplanProposal
from app.db.session import SessionLocal
from app.integrations.mock import providers as mock_providers
from app.main import app

_original_init = mock_providers.MockMobilityProvider.__init__


def _patched_init(self, place_lookup=None, *, strict=False):
    _original_init(self, place_lookup, strict=strict)
    self._fixture["minutes"].setdefault("place-food-hall|place-river-cruise", 20)


mock_providers.MockMobilityProvider.__init__ = _patched_init


def active(*, booking=False):
    client = TestClient(app)
    jid = client.post("/api/v1/demo/reset").json()["journey_id"]
    plan = client.post(f"/api/v1/journeys/{jid}/plans/generate", json={"candidate_count": 1}).json()[0]
    assert client.post(f"/api/v1/journeys/{jid}/plans/{plan['id']}/select").status_code == 200
    booking_row = None
    if booking:
        activity = next(item for item in plan["activities"] if item["place_id"] == "place-river-cruise")
        booking_row = client.post(f"/api/v1/journeys/{jid}/bookings", json={"activity_id": activity["id"]}).json()
    assert client.post(f"/api/v1/journeys/{jid}/start").status_code == 200
    return client, jid, plan, booking_row


def proposal(client, jid):
    event = client.post(f"/api/v1/journeys/{jid}/events", json={"event_type": "SCHEDULE_DELAY", "payload": {"delay_minutes": 10}}).json()
    prop = client.post(f"/api/v1/journeys/{jid}/replans", json={"trigger_event_id": event["id"], "candidate_count": 1}).json()
    return event, prop


def race(calls):
    barrier = threading.Barrier(len(calls))
    def invoke(fn):
        barrier.wait()
        try:
            response = fn()
            return {"status": response.status_code, "body": response.json() if response.headers.get("content-type", "").startswith("application/json") else response.text}
        except Exception as exc:  # evidence, not suppression
            return {"exception": type(exc).__name__, "message": str(exc)}
    with ThreadPoolExecutor(max_workers=len(calls)) as pool:
        return list(pool.map(invoke, calls))


def coherent(jid):
    with SessionLocal() as session:
        journey = session.get(Journey, jid)
        active_plans = session.scalars(select(PlanVersion).where(PlanVersion.journey_id == jid, PlanVersion.status == "ACTIVE")).all()
        accepted = session.scalars(select(ReplanProposal).where(ReplanProposal.journey_id == jid, ReplanProposal.status == "ACCEPTED")).all()
        commitments = session.scalars(select(Commitment).where(Commitment.journey_id == jid, Commitment.status == "ACTIVE")).all()
        dangling = []
        for item in commitments:
            if item.activity_id:
                activity = session.get(Activity, item.activity_id)
                if activity is None or activity.plan_version_id != journey.active_plan_version_id:
                    dangling.append(item.id)
        return {"active_plan_ids": [p.id for p in active_plans], "journey_active_plan_id": journey.active_plan_version_id, "accepted_ids": [p.id for p in accepted], "dangling_commitments": dangling}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    results = []

    client, jid, _plan, _ = active()
    _event, prop = proposal(client, jid)
    same_key = f"race-same-{uuid4()}"
    responses = race([lambda: TestClient(app).post(f"/api/v1/replans/{prop['id']}/accept", headers={"Idempotency-Key": same_key}) for _ in range(2)])
    results.append({"scenario": "same-proposal-same-key", "responses": responses, "state": coherent(jid)})

    client, jid, _plan, _ = active()
    _event, prop = proposal(client, jid)
    responses = race([
        lambda: TestClient(app).post(f"/api/v1/replans/{prop['id']}/accept", headers={"Idempotency-Key": f"race-a-{uuid4()}"}),
        lambda: TestClient(app).post(f"/api/v1/replans/{prop['id']}/accept", headers={"Idempotency-Key": f"race-b-{uuid4()}"}),
    ])
    results.append({"scenario": "same-proposal-different-keys", "responses": responses, "state": coherent(jid)})

    client, jid, _plan, _ = active()
    event, p1 = proposal(client, jid)
    p2 = client.post(f"/api/v1/journeys/{jid}/replans", json={"trigger_event_id": event["id"], "candidate_count": 1}).json()
    responses = race([
        lambda: TestClient(app).post(f"/api/v1/replans/{p1['id']}/accept", headers={"Idempotency-Key": f"race-p1-{uuid4()}"}),
        lambda: TestClient(app).post(f"/api/v1/replans/{p2['id']}/accept", headers={"Idempotency-Key": f"race-p2-{uuid4()}"}),
    ])
    results.append({"scenario": "competing-proposals", "responses": responses, "state": coherent(jid)})

    client, jid, _plan, booking = active(booking=True)
    _event, prop = proposal(client, jid)
    capture_key = f"race-capture-{uuid4()}"
    responses = race([
        lambda: TestClient(app).post(f"/api/v1/replans/{prop['id']}/accept", headers={"Idempotency-Key": f"race-accept-{uuid4()}"}),
        lambda: TestClient(app).post(f"/api/v1/journeys/{jid}/transactions", json={"booking_id": booking["id"], "transaction_type": "CAPTURE", "amount": booking["amount"]}, headers={"Idempotency-Key": capture_key}),
        lambda: TestClient(app).get(f"/api/v1/journeys/{jid}/experience"),
    ])
    results.append({"scenario": "booking-capture-vs-accept-plus-read", "responses": responses, "state": coherent(jid)})

    client, jid, _plan, _ = active()
    _event, prop = proposal(client, jid)
    key = f"race-restart-{uuid4()}"
    first = client.post(f"/api/v1/replans/{prop['id']}/accept", headers={"Idempotency-Key": key})
    client.close()
    second = TestClient(app).post(f"/api/v1/replans/{prop['id']}/accept", headers={"Idempotency-Key": key})
    results.append({"scenario": "restart-and-retry", "responses": [{"status": first.status_code, "body": first.json()}, {"status": second.status_code, "body": second.json()}], "equal": first.json() == second.json(), "state": coherent(jid)})

    defects = []
    for item in results:
        state = item["state"]
        if len(state["active_plan_ids"]) != 1 or state["active_plan_ids"][0] != state["journey_active_plan_id"] or len(state["accepted_ids"]) > 1 or state["dangling_commitments"]:
            defects.append(item["scenario"])
        if any("exception" in response for response in item["responses"]):
            defects.append(item["scenario"] + ":exception")
    payload = {"scenarios": results, "defects": sorted(set(defects))}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, default=str) + "\n", encoding="utf-8")
    print(json.dumps({"scenario_count": len(results), "defects": payload["defects"]}))
    return 0 if not defects else 1


if __name__ == "__main__":
    raise SystemExit(main())
