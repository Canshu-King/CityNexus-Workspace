from __future__ import annotations

import pytest
from app.db.session import ensure_schema, make_engine
from app.main import app
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker

client = TestClient(app)
JOURNEY_ID = "22222222-2222-4222-8222-222222222222"
TRAVELER_ID = "11111111-1111-4111-8111-111111111111"


def reset() -> None:
    response = client.post("/api/v1/demo/reset")
    assert response.status_code == 200


def test_cnx_i_001_schema_from_empty_sqlite():
    empty_engine = make_engine("sqlite://")
    ensure_schema(empty_engine)
    LocalSession = sessionmaker(bind=empty_engine)
    with LocalSession() as session:
        tables = session.execute(text("SELECT name FROM sqlite_master WHERE type='table'"))
        names = {row[0] for row in tables}
    assert {
        "travelers",
        "journeys",
        "plan_versions",
        "activities",
        "places",
        "city_services",
    } <= names


def test_cnx_i_002_foreign_keys_enabled():
    empty_engine = make_engine("sqlite://")
    ensure_schema(empty_engine)
    LocalSession = sessionmaker(bind=empty_engine)
    with LocalSession() as session:
        assert session.execute(text("PRAGMA foreign_keys")).scalar() == 1
        with pytest.raises(IntegrityError):
            session.execute(
                text(
                    "INSERT INTO preferences (id, traveler_id, category, preference_key, value_json, weight, source, created_at, updated_at) VALUES ('x', 'missing', 'interest', 'art', 'true', 1, 'user', '2026-01-01T00:00:00+00:00', '2026-01-01T00:00:00+00:00')"
                )
            )
            session.commit()


def test_cnx_i_003_create_and_get_traveler():
    reset()
    payload = {"display_name": "Taylor", "timezone": "Asia/Shanghai"}
    created = client.post("/api/v1/travelers", json=payload)
    assert created.status_code == 201
    assert (
        client.get(f"/api/v1/travelers/{created.json()['id']}").json()["display_name"] == "Taylor"
    )


def test_cnx_i_004_replace_preferences():
    reset()
    response = client.put(
        f"/api/v1/travelers/{TRAVELER_ID}/preferences",
        json=[{"category": "interest", "key": "art", "value": True, "weight": 0.8}],
    )
    assert response.status_code == 200
    assert client.get(f"/api/v1/travelers/{TRAVELER_ID}/preferences").json()[0]["key"] == "art"


def test_cnx_i_005_valid_journey_is_draft():
    reset()
    payload = {
        "traveler_id": TRAVELER_ID,
        "title": "Test",
        "city_code": "CNX-DEMO",
        "timezone": "Asia/Shanghai",
        "start_at": "2026-10-10T09:00:00+08:00",
        "end_at": "2026-10-10T19:00:00+08:00",
        "budget": {"amount_minor": 50000, "currency": "CNY"},
    }
    response = client.post("/api/v1/journeys", json=payload)
    assert response.status_code == 201 and response.json()["status"] == "DRAFT"


def test_cnx_i_006_end_before_start_is_422():
    reset()
    payload = {
        "traveler_id": TRAVELER_ID,
        "title": "Invalid",
        "city_code": "CNX-DEMO",
        "timezone": "Asia/Shanghai",
        "start_at": "2026-10-10T19:00:00+08:00",
        "end_at": "2026-10-10T09:00:00+08:00",
        "budget": {"amount_minor": 50000, "currency": "CNY"},
    }
    assert client.post("/api/v1/journeys", json=payload).status_code == 422


def test_cnx_i_007_hard_budget_constraint_persists():
    reset()
    response = client.post(
        f"/api/v1/journeys/{JOURNEY_ID}/constraints",
        json={
            "kind": "HARD",
            "category": "budget",
            "rule_code": "BUDGET_MAX",
            "params": {"amount_minor": 40000},
            "weight": 1,
        },
    )
    assert response.status_code == 201 and response.json()["kind"] == "HARD"


def test_cnx_i_008_places_are_deterministic():
    reset()
    first = client.get("/api/v1/places?city_code=CNX-DEMO").json()
    second = client.get("/api/v1/places?city_code=CNX-DEMO").json()
    assert first == second and len(first) == 8


def test_cnx_i_009_generate_at_least_two_feasible_candidates():
    reset()
    response = client.post(
        f"/api/v1/journeys/{JOURNEY_ID}/plans/generate",
        json={"planning_mode": "balanced", "candidate_count": 3},
    )
    assert response.status_code == 201
    plans = response.json()
    assert len(plans) >= 2
    assert all(
        plan["status"] == "CANDIDATE"
        and plan["activities"]
        and plan["score_breakdown"]["total"] >= 0
        for plan in plans
    )


def test_cnx_i_010_select_candidate_plans_journey():
    reset()
    plans = client.post(
        f"/api/v1/journeys/{JOURNEY_ID}/plans/generate", json={"candidate_count": 2}
    ).json()
    response = client.post(f"/api/v1/journeys/{JOURNEY_ID}/plans/{plans[0]['id']}/select")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "PLANNED" and body["active_plan_version_id"] == plans[0]["id"]
