"""CX-SOL-001 — the execution cursor is an assertion about identity, not a hint.

Before this pass the projection had one branch for "the cursor is absent" and
"the cursor names something that is not on this plan", and that branch was
*fall back to the first pending activity*.  The two cases are not alike:

    null cursor      -> the journey has started and nothing is done yet.  Showing
                        the first pending step is the truth.
    unresolvable     -> the record contradicts itself.  Showing the first pending
                        step is a fabrication the traveller will act on: they are
                        told they are at the museum when the authoritative row
                        says they were at a dinner that no longer exists.

So the cursor now has three states (VALID / ABSENT_FALLBACK / STALE), STALE
projects no Now, no Next and no NextLeg, and every consumer can see which state
it is in instead of inferring one from list order.

The second half of this file is a differential oracle: an independent reference
projection computed straight from the Activity and JourneyLeg rows is compared
against what the product serves, field by field, for every cursor state.  Where
authoritative truth exists, zero divergence is allowed; where it does not, the
product must fail closed rather than produce an equivalent-looking value.
"""

from __future__ import annotations

from typing import Any
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy import select

import app.main as main_module
from app.db.models import Activity, Journey, JourneyLeg
from app.db.session import SessionLocal
from app.operations.v9 import refresh_offline_snapshot

client = TestClient(main_module.app)

TERMINAL = {"COMPLETED", "SKIPPED", "CANCELLED"}


# --------------------------------------------------------------------------
# fixture helpers, all through the product's own endpoints
# --------------------------------------------------------------------------
def _started_journey() -> tuple[str, list[dict[str, Any]]]:
    journey_id = client.post("/api/v1/demo/reset").json()["journey_id"]
    plan = client.post(
        f"/api/v1/journeys/{journey_id}/plans/generate", json={"candidate_count": 1}
    ).json()[0]
    assert client.post(
        f"/api/v1/journeys/{journey_id}/plans/{plan['id']}/select"
    ).status_code == 200
    assert client.post(f"/api/v1/journeys/{journey_id}/start").status_code == 200
    return journey_id, plan["activities"]


def _set_cursor(journey_id: str, cursor: str | None, statuses: dict[str, str] = {}) -> None:
    """Move the persisted cursor, then refresh the projection as the product does."""
    with SessionLocal() as session:
        journey = session.get(Journey, journey_id)
        assert journey is not None
        journey.current_activity_id = cursor
        activities = session.scalars(
            select(Activity)
            .where(Activity.plan_version_id == journey.active_plan_version_id)
            .order_by(Activity.sequence_no)
        ).all()
        for item in activities:
            if item.id in statuses:
                item.status = statuses[item.id]
        refresh_offline_snapshot(session, journey)
        session.commit()


def _plan_rows(journey_id: str) -> tuple[list[Activity], list[JourneyLeg], str | None]:
    with SessionLocal() as session:
        journey = session.get(Journey, journey_id)
        assert journey is not None
        activities = list(
            session.scalars(
                select(Activity)
                .where(Activity.plan_version_id == journey.active_plan_version_id)
                .order_by(Activity.sequence_no)
            ).all()
        )
        legs = list(
            session.scalars(
                select(JourneyLeg)
                .where(JourneyLeg.plan_version_id == journey.active_plan_version_id)
                .order_by(JourneyLeg.sequence_no)
            ).all()
        )
        return activities, legs, journey.current_activity_id



def _off_plan_activity_id(journey_id: str) -> str:
    """A real Activity row that is not on the active plan.

    The foreign key on `journeys.current_activity_id` means a made-up id cannot
    be persisted at all, so it cannot be the test.  A pointer into another plan
    of the same journey satisfies the key and is still stale for the plan being
    executed, which is exactly the state the guard has to survive.
    """
    candidates = client.post(
        f"/api/v1/journeys/{journey_id}/plans/generate", json={"candidate_count": 3}
    ).json()
    with SessionLocal() as session:
        journey = session.get(Journey, journey_id)
        assert journey is not None
        for plan in candidates:
            if plan["id"] == journey.active_plan_version_id:
                continue
            for item in plan["activities"]:
                return str(item["id"])
    raise AssertionError("no off-plan activity is available to act as a stale cursor")


def _served_projection(journey_id: str) -> dict[str, Any]:
    """What the product actually serves to a client, after a projection refresh."""
    with SessionLocal() as session:
        journey = session.get(Journey, journey_id)
        refresh_offline_snapshot(session, journey)
        session.commit()
    snapshot = client.get(f"/api/v1/journeys/{journey_id}/offline-snapshot").json()["snapshot"]
    return snapshot["execution"]


def _reference_projection(journey_id: str) -> dict[str, Any]:
    """Recompute the window straight from the rows, without the product's code."""
    activities, legs, cursor = _plan_rows(journey_id)
    by_id = {item.id: index for index, item in enumerate(activities)}
    if cursor is None:
        index = next(
            (i for i, item in enumerate(activities) if item.status not in TERMINAL),
            len(activities),
        )
        status = "ABSENT_FALLBACK"
    elif cursor not in by_id:
        index = len(activities)
        status = "STALE"
    else:
        index = by_id[cursor]
        status = "VALID"
    now = (
        activities[index]
        if index < len(activities) and activities[index].status not in TERMINAL
        else None
    )
    nxt = next(
        (item for item in activities[index + 1 :] if item.status not in TERMINAL), None
    )
    leg = legs[index] if 0 <= index < len(legs) else None
    return {
        "cursor_status": status,
        "persisted_cursor": cursor,
        "now_activity_id": now.id if now else None,
        "next_activity_id": nxt.id if nxt else None,
        "next_leg_id": leg.id if leg else None,
        "next_mode": leg.mode if leg else "NONE",
        "next_eta_min": leg.duration_min if leg else 0,
    }


# --------------------------------------------------------------------------
# A. the truth table
# --------------------------------------------------------------------------
def test_null_cursor_is_a_legal_pre_execution_state_and_projects_the_first_step() -> None:
    journey_id, activities = _started_journey()
    _set_cursor(journey_id, None)

    served = _served_projection(journey_id)
    assert served["cursor_status"] == "ABSENT_FALLBACK"
    # Falling back is allowed here, and it is the truth: nothing has happened yet.
    assert served["now_activity_id"] == activities[0]["id"]
    assert served["next_activity_id"] == activities[1]["id"]


def test_valid_cursor_projects_exactly_that_activity_and_not_its_neighbours() -> None:
    journey_id, activities = _started_journey()
    target = activities[2]["id"]
    _set_cursor(journey_id, target)

    served = _served_projection(journey_id)
    assert served["cursor_status"] == "VALID"
    assert served["persisted_cursor"] == target
    assert served["now_activity_id"] == target
    assert served["next_activity_id"] == activities[3]["id"]


def test_cursor_naming_an_off_plan_activity_fails_closed_and_invents_nothing() -> None:
    journey_id, _ = _started_journey()
    _set_cursor(journey_id, _off_plan_activity_id(journey_id))

    served = _served_projection(journey_id)
    assert served["cursor_status"] == "STALE"
    # The three fabricated fields are the defect: each one looks plausible and
    # none of them is supported by the record.
    assert served["now_activity_id"] is None
    assert served["next_activity_id"] is None
    assert served["next_leg_id"] is None
    assert served["now_state"] == "STALE_CURSOR"
    assert served["next_mode"] == "NONE"
    assert served["next_eta_min"] == 0


def test_cursor_left_on_a_superseded_plan_after_a_replan_fails_closed() -> None:
    """The realistic stale case: the cursor still names a real row, but a row on
    the plan the accepted recovery replaced."""
    journey_id, activities = _started_journey()
    base_cursor = activities[1]["id"]
    _set_cursor(journey_id, base_cursor)

    event = client.post(
        f"/api/v1/journeys/{journey_id}/events",
        json={
            "event_type": "CLOSURE",
            "severity": "MAJOR",
            "affected_activity_id": activities[3]["id"],
            "occurred_at": "2026-10-10T13:25:00+08:00",
            "payload": {"reason": "stale cursor after replan"},
        },
    ).json()
    client.post(
        "/api/v1/agent/tools/request_replan",
        json={
            "request_id": f"stale-{event['id']}",
            "agent_id": "citynexus-local-agent",
            "journey_id": journey_id,
            "trigger_event_id": event["id"],
            "candidate_count": 3,
        },
    )
    proposals = client.get(f"/api/v1/journeys/{journey_id}/replans").json()
    proposal = next(
        item
        for item in proposals
        if item.get("trigger_event_id") == event["id"] and item.get("status") == "PRESENTED"
    )
    assert client.post(
        f"/api/v1/replans/{proposal['id']}/accept",
        headers={"Idempotency-Key": f"stale-accept-{proposal['id']}"},
    ).status_code == 200

    # A correctly carried-forward cursor is VALID on the child plan.
    served = _served_projection(journey_id)
    assert served["cursor_status"] == "VALID", (
        "acceptance did not carry the execution position onto the child plan, so the "
        "traveller's current step was silently reset or dropped"
    )

    # Now simulate the failure mode the guard exists for: a cursor that still
    # names the superseded plan's row.
    _set_cursor(journey_id, base_cursor)
    stale = _served_projection(journey_id)
    assert stale["cursor_status"] == "STALE"
    assert stale["now_activity_id"] is None
    assert stale["next_activity_id"] is None


def test_experience_projection_reports_the_cursor_state_next_to_the_cursor() -> None:
    journey_id, activities = _started_journey()
    _set_cursor(journey_id, _off_plan_activity_id(journey_id))

    plan = client.get(f"/api/v1/journeys/{journey_id}/experience").json()["active_plan"]
    listed = {item["id"] for item in plan["activities"]}
    assert plan["current_activity_id"] not in listed
    assert plan["cursor_status"] == "STALE", (
        "/experience served a cursor and an activity list that do not intersect, with "
        "no way for the consumer to notice"
    )
    # The lifecycle status is what lets a client tell "done" from "pending" without
    # re-deriving it from list order.
    assert all(item.get("status") for item in plan["activities"])


def test_edge_device_is_told_the_position_is_unresolved_not_that_the_journey_ended() -> None:
    journey_id, _ = _started_journey()
    device = client.post(
        f"/api/v1/journeys/{journey_id}/edge/devices",
        json={"display_name": "oracle device"},
    ).json()
    headers = {"X-Edge-Token": device["device_token"]}

    _set_cursor(journey_id, _off_plan_activity_id(journey_id))
    snapshot = client.get(
        f"/api/v1/edge/devices/{device['device_id']}/journey-snapshot", headers=headers
    ).json()

    assert snapshot["cursor_status"] == "STALE"
    assert snapshot["now_title"] == "Execution position unresolved"
    # "Journey complete" is the pre-fix wording and it is a lie: the journey is
    # active, the record is inconsistent.
    assert snapshot["next_title"] == "Next step unavailable"
    assert snapshot["now_state"] == "STALE_CURSOR"


# --------------------------------------------------------------------------
# H. differential oracle
# --------------------------------------------------------------------------
def _oracle_case(journey_id: str) -> None:
    reference = _reference_projection(journey_id)
    served = _served_projection(journey_id)
    diverging = {
        field: (reference[field], served.get(field))
        for field in (
            "cursor_status",
            "now_activity_id",
            "next_activity_id",
            "next_leg_id",
            "next_mode",
            "next_eta_min",
        )
        if reference[field] != served.get(field)
    }
    assert not diverging, (
        f"the product projection disagrees with the rows for cursor "
        f"{reference['cursor_status']}: {diverging}"
    )


def test_projection_matches_the_reference_for_every_cursor_state() -> None:
    for label, mutate in (
        ("valid", lambda acts, jid: _set_cursor(jid, acts[1]["id"])),
        ("null", lambda acts, jid: _set_cursor(jid, None)),
        (
            "off-plan cursor",
            lambda acts, jid: _set_cursor(jid, _off_plan_activity_id(jid)),
        ),
        (
            "cursor on a terminal step",
            lambda acts, jid: _set_cursor(
                jid, acts[1]["id"], {acts[1]["id"]: "COMPLETED"}
            ),
        ),
        (
            "null cursor with the first steps completed",
            lambda acts, jid: _set_cursor(
                jid, None, {acts[0]["id"]: "COMPLETED", acts[1]["id"]: "SKIPPED"}
            ),
        ),
    ):
        journey_id, activities = _started_journey()
        mutate(activities, journey_id)
        _oracle_case(journey_id)
        assert _reference_projection(journey_id)["cursor_status"] is not None, label


def test_projection_matches_the_reference_after_an_accepted_replan() -> None:
    journey_id, activities = _started_journey()
    _set_cursor(journey_id, activities[1]["id"])
    event = client.post(
        f"/api/v1/journeys/{journey_id}/events",
        json={
            "event_type": "CLOSURE",
            "severity": "MAJOR",
            "affected_activity_id": activities[3]["id"],
            "occurred_at": "2026-10-10T13:25:00+08:00",
            "payload": {"reason": "post-replan oracle"},
        },
    ).json()
    client.post(
        "/api/v1/agent/tools/request_replan",
        json={
            "request_id": f"oracle-{event['id']}",
            "agent_id": "citynexus-local-agent",
            "journey_id": journey_id,
            "trigger_event_id": event["id"],
            "candidate_count": 3,
        },
    )
    proposal = next(
        item
        for item in client.get(f"/api/v1/journeys/{journey_id}/replans").json()
        if item.get("trigger_event_id") == event["id"] and item.get("status") == "PRESENTED"
    )
    assert client.post(
        f"/api/v1/replans/{proposal['id']}/accept",
        headers={"Idempotency-Key": f"oracle-accept-{proposal['id']}"},
    ).status_code == 200
    _oracle_case(journey_id)
