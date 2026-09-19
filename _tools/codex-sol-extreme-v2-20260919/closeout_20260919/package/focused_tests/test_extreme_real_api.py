"""Focused real-API regressions for Extreme Verification v2.

These tests execute the production FastAPI routes and SQLAlchemy persistence.
The database URL is supplied by the runner before importing the application.
"""
from __future__ import annotations

import sys
from pathlib import Path
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

BACKEND_TESTS = Path(__file__).resolve().parents[1] / "snapshot" / "citynexus" / "backend" / "tests"
sys.path.insert(0, str(BACKEND_TESTS))

from _qoder_explicit_demo_mobility import WP06_POSTGATE_MOBILITY, seed_module_mobility  # noqa: E402
from app.db.models import Activity, Commitment, Event, Journey, PlanVersion, ReplanProposal  # noqa: E402
from app.db.session import SessionLocal  # noqa: E402
from app.main import app  # noqa: E402
from app.operations.v9 import refresh_offline_snapshot  # noqa: E402

client = TestClient(app)


@pytest.fixture(autouse=True)
def explicit_demo_mobility(monkeypatch):
    seed_module_mobility(monkeypatch, WP06_POSTGATE_MOBILITY)


def active_journey(*, protected_booking: bool = False) -> tuple[str, dict]:
    ids = client.post("/api/v1/demo/reset").json()
    journey_id = ids["journey_id"]
    response = client.post(
        f"/api/v1/journeys/{journey_id}/plans/generate", json={"candidate_count": 1}
    )
    assert response.status_code == 201, response.text
    plan = response.json()[0]
    assert client.post(f"/api/v1/journeys/{journey_id}/plans/{plan['id']}/select").status_code == 200
    if protected_booking:
        activity = next(item for item in plan["activities"] if item["place_id"] == "place-river-cruise")
        booking = client.post(
            f"/api/v1/journeys/{journey_id}/bookings", json={"activity_id": activity["id"]}
        )
        assert booking.status_code == 201, booking.text
        capture = client.post(
            f"/api/v1/journeys/{journey_id}/transactions",
            json={"booking_id": booking.json()["id"], "transaction_type": "CAPTURE", "amount": booking.json()["amount"]},
            headers={"Idempotency-Key": f"extreme-booking-{uuid4()}"},
        )
        assert capture.status_code == 201, capture.text
    assert client.post(f"/api/v1/journeys/{journey_id}/start").status_code == 200
    return journey_id, plan


def create_event(journey_id: str, delay: int = 10) -> dict:
    response = client.post(
        f"/api/v1/journeys/{journey_id}/events",
        json={"event_type": "SCHEDULE_DELAY", "payload": {"delay_minutes": delay}},
    )
    assert response.status_code == 201, response.text
    return response.json()


def create_proposal(journey_id: str, event_id: str) -> dict:
    response = client.post(
        f"/api/v1/journeys/{journey_id}/replans",
        json={"trigger_event_id": event_id, "candidate_count": 1},
    )
    assert response.status_code == 201, response.text
    return response.json()


def test_present_but_unknown_cursor_fails_closed_across_real_projections() -> None:
    journey_id, plan = active_journey()
    # Foreign keys prevent a totally nonexistent cursor.  The reachable stale
    # shape is an existing Activity from a non-active candidate/superseded plan.
    candidate = client.post(
        f"/api/v1/journeys/{journey_id}/plans/generate", json={"candidate_count": 1}
    )
    assert candidate.status_code == 201, candidate.text
    stale = candidate.json()[0]["activities"][0]["id"]
    with SessionLocal() as session:
        journey = session.get(Journey, journey_id)
        journey.current_activity_id = stale
        refresh_offline_snapshot(session, journey)
        session.commit()

    experience = client.get(f"/api/v1/journeys/{journey_id}/experience").json()
    assert experience["active_plan"]["current_activity_id"] == stale
    assert experience["active_plan"]["activities"][0]["id"] != stale

    twin = client.get(f"/api/v1/journeys/{journey_id}/twin").json()
    execution = twin["context"]["execution"]
    assert execution["cursor_status"] == "STALE"
    assert execution["now_activity_id"] is None
    assert execution["next_activity_id"] is None
    assert execution["now_state"] == "STALE_CURSOR"

    offline = client.get(f"/api/v1/journeys/{journey_id}/offline-snapshot").json()
    offline_execution = offline["snapshot"]["execution"]
    assert offline_execution["cursor_status"] == "STALE"
    assert offline_execution["now_activity_id"] is None
    assert offline_execution["next_activity_id"] is None

    assert plan["activities"][0]["id"] not in {
        execution["now_activity_id"], offline_execution["now_activity_id"]
    }


def test_absent_cursor_allows_only_preexecution_fallback() -> None:
    ids = client.post("/api/v1/demo/reset").json()
    journey_id = ids["journey_id"]
    plan = client.post(
        f"/api/v1/journeys/{journey_id}/plans/generate", json={"candidate_count": 1}
    ).json()[0]
    assert client.post(f"/api/v1/journeys/{journey_id}/plans/{plan['id']}/select").status_code == 200
    twin = client.get(f"/api/v1/journeys/{journey_id}/twin").json()
    execution = twin["context"]["execution"]
    assert execution["cursor_status"] == "ABSENT_FALLBACK"
    assert execution["now_activity_id"] == plan["activities"][0]["id"]


def test_final_current_activity_has_no_fabricated_next_or_leg() -> None:
    journey_id, plan = active_journey()
    final_id = plan["activities"][-1]["id"]
    with SessionLocal() as session:
        journey = session.get(Journey, journey_id)
        journey.current_activity_id = final_id
        for item in session.scalars(
            select(Activity).where(Activity.plan_version_id == journey.active_plan_version_id)
        ).all():
            item.status = "ACTIVE" if item.id == final_id else "COMPLETED"
        session.commit()
    execution = client.get(f"/api/v1/journeys/{journey_id}/twin").json()["context"]["execution"]
    assert execution["now_activity_id"] == final_id
    assert execution["next_activity_id"] is None
    assert execution["next_mode"] == "NONE"
    assert execution["next_eta_min"] == 0


def test_accepted_proposal_closes_only_its_linked_trigger() -> None:
    journey_id, _ = active_journey()
    linked = create_event(journey_id, 7)
    unrelated = create_event(journey_id, 13)
    proposal = create_proposal(journey_id, linked["id"])
    accepted = client.post(
        f"/api/v1/replans/{proposal['id']}/accept",
        headers={"Idempotency-Key": f"extreme-linked-{uuid4()}"},
    )
    assert accepted.status_code == 200, accepted.text
    with SessionLocal() as session:
        accepted_row = session.get(ReplanProposal, proposal["id"])
        linked_row = session.get(Event, linked["id"])
        unrelated_row = session.get(Event, unrelated["id"])
        assert accepted_row.status == "ACCEPTED"
        assert accepted_row.trigger_event_id == linked_row.id
        assert linked_row.status == "ACKNOWLEDGED"
        assert unrelated_row.status == "DETECTED"


def test_protected_commitment_survives_accept_and_points_into_new_active_plan() -> None:
    journey_id, old_plan = active_journey(protected_booking=True)
    event = create_event(journey_id)
    proposal = create_proposal(journey_id, event["id"])
    accepted = client.post(
        f"/api/v1/replans/{proposal['id']}/accept",
        headers={"Idempotency-Key": f"extreme-c4-{uuid4()}"},
    )
    assert accepted.status_code == 200, accepted.text
    new_plan = accepted.json()["journey"]["active_plan_version_id"]
    assert new_plan != old_plan["id"]
    with SessionLocal() as session:
        commitments = session.scalars(
            select(Commitment).where(
                Commitment.journey_id == journey_id,
                Commitment.status == "ACTIVE",
                Commitment.level == "C4_Anchored",
            )
        ).all()
        assert commitments
        for commitment in commitments:
            activity = session.get(Activity, commitment.activity_id)
            assert activity is not None
            assert activity.plan_version_id == new_plan


def test_same_accept_key_replays_one_persisted_authoritative_result() -> None:
    journey_id, _ = active_journey()
    event = create_event(journey_id)
    proposal = create_proposal(journey_id, event["id"])
    headers = {"Idempotency-Key": f"extreme-replay-{uuid4()}"}
    first = client.post(f"/api/v1/replans/{proposal['id']}/accept", headers=headers)
    second = client.post(f"/api/v1/replans/{proposal['id']}/accept", headers=headers)
    assert first.status_code == second.status_code == 200
    assert first.json() == second.json()
    with SessionLocal() as session:
        active = session.scalars(
            select(PlanVersion).where(PlanVersion.journey_id == journey_id, PlanVersion.status == "ACTIVE")
        ).all()
        assert len(active) == 1
