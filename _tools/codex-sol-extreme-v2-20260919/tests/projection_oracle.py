#!/usr/bin/env python3
"""Differential oracle over real CityNexus persistence and API projections."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.db.models import Activity, Journey, JourneyLeg
from app.db.session import SessionLocal
from app.main import app
from app.operations.v9 import refresh_offline_snapshot


def setup(client: TestClient) -> tuple[str, dict]:
    journey_id = client.post("/api/v1/demo/reset").json()["journey_id"]
    plan = client.post(
        f"/api/v1/journeys/{journey_id}/plans/generate", json={"candidate_count": 1}
    ).json()[0]
    assert client.post(f"/api/v1/journeys/{journey_id}/plans/{plan['id']}/select").status_code == 200
    assert client.post(f"/api/v1/journeys/{journey_id}/start").status_code == 200
    return journey_id, plan


def set_cursor(journey_id: str, cursor: str | None, statuses: list[str]) -> None:
    with SessionLocal() as session:
        journey = session.get(Journey, journey_id)
        activities = session.scalars(
            select(Activity).where(Activity.plan_version_id == journey.active_plan_version_id).order_by(Activity.sequence_no)
        ).all()
        journey.current_activity_id = cursor
        for item, status in zip(activities, statuses):
            item.status = status
        refresh_offline_snapshot(session, journey)
        session.commit()


def remove_all_plan_activities(journey_id: str) -> None:
    with SessionLocal() as session:
        journey = session.get(Journey, journey_id)
        journey.current_activity_id = None
        for leg in session.scalars(
            select(JourneyLeg).where(JourneyLeg.plan_version_id == journey.active_plan_version_id)
        ).all():
            session.delete(leg)
        for activity in session.scalars(
            select(Activity).where(Activity.plan_version_id == journey.active_plan_version_id)
        ).all():
            session.delete(activity)
        session.flush()
        refresh_offline_snapshot(session, journey)
        session.commit()


def authoritative(journey_id: str) -> dict:
    with SessionLocal() as session:
        journey = session.get(Journey, journey_id)
        activities = session.scalars(
            select(Activity).where(Activity.plan_version_id == journey.active_plan_version_id).order_by(Activity.sequence_no)
        ).all()
        legs = session.scalars(
            select(JourneyLeg).where(JourneyLeg.plan_version_id == journey.active_plan_version_id).order_by(JourneyLeg.sequence_no)
        ).all()
        by_id = {item.id: index for index, item in enumerate(activities)}
        if journey.current_activity_id is None:
            index = next((i for i, item in enumerate(activities) if item.status not in {"COMPLETED", "SKIPPED", "CANCELLED"}), len(activities))
            cursor_status = "ABSENT_FALLBACK"
        elif journey.current_activity_id not in by_id:
            index = len(activities)
            cursor_status = "STALE"
        else:
            index = by_id[journey.current_activity_id]
            cursor_status = "VALID"
        now = activities[index] if index < len(activities) and activities[index].status not in {"COMPLETED", "SKIPPED", "CANCELLED"} else None
        next_item = next((item for item in activities[index + 1:] if item.status not in {"COMPLETED", "SKIPPED", "CANCELLED"}), None)
        next_leg = legs[index] if now is not None and next_item is not None and index < len(legs) else None
        return {
            "active_plan_id": journey.active_plan_version_id,
            "persisted_cursor": journey.current_activity_id,
            "cursor_status": cursor_status,
            "now_activity_id": now.id if now else None,
            "next_activity_id": next_item.id if next_item else None,
            "next_leg_id": next_leg.id if next_leg else None,
        }


def compare_case(client: TestClient, journey_id: str, name: str) -> dict:
    oracle = authoritative(journey_id)
    experience = client.get(f"/api/v1/journeys/{journey_id}/experience").json()
    twin = client.get(f"/api/v1/journeys/{journey_id}/twin").json()
    offline = client.get(f"/api/v1/journeys/{journey_id}/offline-snapshot").json()
    clock = client.get(f"/api/v1/journeys/{journey_id}/execution-clock").json()
    ex = twin["context"]["execution"]
    off = offline["snapshot"]["execution"]
    projections = {
        "experience": {"active_plan_id": experience["active_plan"]["id"], "persisted_cursor": experience["active_plan"]["current_activity_id"]},
        "twin": {"active_plan_id": twin["active_plan_version_id"], "cursor_status": ex.get("cursor_status"), "now_activity_id": ex["now_activity_id"], "next_activity_id": ex["next_activity_id"]},
        "offline": {"active_plan_id": offline["snapshot"]["active_plan_version_id"], "cursor_status": off.get("cursor_status"), "now_activity_id": off["now_activity_id"], "next_activity_id": off["next_activity_id"]},
        "execution_clock": {"persisted_cursor": clock["current_activity_id"]},
    }
    divergences = []
    for projection in ("experience", "twin", "offline"):
        if projections[projection].get("active_plan_id") != oracle["active_plan_id"]:
            divergences.append(f"{projection}.active_plan_id")
    for projection in ("experience", "execution_clock"):
        if projections[projection]["persisted_cursor"] != oracle["persisted_cursor"]:
            divergences.append(f"{projection}.persisted_cursor")
    for projection in ("twin", "offline"):
        for field in ("cursor_status", "now_activity_id", "next_activity_id"):
            if projections[projection].get(field) != oracle[field]:
                divergences.append(f"{projection}.{field}")
    return {"case": name, "oracle": oracle, "projections": projections, "divergences": divergences}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    client = TestClient(app)
    journey_id, plan = setup(client)
    ids = [item["id"] for item in plan["activities"]]
    n = len(ids)
    cases = []
    set_cursor(journey_id, None, ["NOT_STARTED"] * n)
    cases.append(compare_case(client, journey_id, "cursor-absent-preexecution"))
    set_cursor(journey_id, None, ["COMPLETED"] + ["NOT_STARTED"] * (n - 1))
    cases.append(compare_case(client, journey_id, "cursor-absent-first-terminal"))
    set_cursor(journey_id, ids[0], ["ACTIVE"] + ["NOT_STARTED"] * (n - 1))
    cases.append(compare_case(client, journey_id, "cursor-first"))
    middle = min(1, n - 1)
    set_cursor(journey_id, ids[middle], ["COMPLETED"] * middle + ["ACTIVE"] + ["NOT_STARTED"] * (n - middle - 1))
    cases.append(compare_case(client, journey_id, "cursor-middle"))
    set_cursor(journey_id, ids[-1], ["COMPLETED"] * (n - 1) + ["ACTIVE"])
    cases.append(compare_case(client, journey_id, "cursor-final"))
    candidate = client.post(
        f"/api/v1/journeys/{journey_id}/plans/generate", json={"candidate_count": 1}
    )
    assert candidate.status_code == 201, candidate.text
    stale_cursor = candidate.json()[0]["activities"][0]["id"]
    set_cursor(journey_id, stale_cursor, ["NOT_STARTED"] * n)
    cases.append(compare_case(client, journey_id, "cursor-stale"))
    remove_all_plan_activities(journey_id)
    cases.append(compare_case(client, journey_id, "no-activities"))
    result = {"journey_id": journey_id, "cases": cases, "divergence_count": sum(len(item["divergences"]) for item in cases)}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"cases": len(cases), "divergence_count": result["divergence_count"]}))
    return 0 if result["divergence_count"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
