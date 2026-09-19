"""Focused regressions added for mutation survivors found by Track J."""
from __future__ import annotations

import types

import pytest
from fastapi.testclient import TestClient

from app.integrations.mobility.snapshot_capture import MobilitySnapshotCaptureError
import app.integrations.mobility.runtime as runtime
from app.main import app


def test_cross_journey_trigger_fails_at_ownership_boundary() -> None:
    client = TestClient(app)
    ids = client.post("/api/v1/demo/reset").json()
    jid = ids["journey_id"]
    plan = client.post(f"/api/v1/journeys/{jid}/plans/generate", json={"candidate_count": 1}).json()[0]
    assert client.post(f"/api/v1/journeys/{jid}/plans/{plan['id']}/select").status_code == 200
    assert client.post(f"/api/v1/journeys/{jid}/start").status_code == 200
    second = client.post(
        "/api/v1/journeys",
        json={
            "traveler_id": ids["traveler_id"],
            "title": "Other Journey",
            "city_code": "CNX-DEMO",
            "timezone": "Asia/Shanghai",
            "start_at": "2026-10-10T09:00:00+08:00",
            "end_at": "2026-10-10T19:00:00+08:00",
            "budget": {"amount_minor": 50000, "currency": "CNY"},
            "planning_mode": "balanced",
        },
    ).json()
    foreign_event = client.post(
        f"/api/v1/journeys/{second['id']}/events",
        json={"event_type": "SCHEDULE_DELAY", "payload": {"delay_minutes": 5}},
    ).json()
    response = client.post(
        f"/api/v1/journeys/{jid}/replans",
        json={"trigger_event_id": foreign_event["id"], "candidate_count": 1},
    )
    assert response.status_code == 422
    body = response.json()
    message = body.get("detail") or body.get("error", {}).get("message")
    assert message == "trigger event is not on this journey", body


class _AlwaysFailLive:
    provider_key = "valhalla"

    def __init__(self, **_kwargs):
        pass

    def status_capabilities(self):
        return {"status": "OK", "has_live_traffic": True}

    def estimate_minutes(self, _origin, _destination):
        raise RuntimeError("live failed")


class _ExplicitMockFallback:
    provider_key = "mock-mobility"

    def __init__(self, **_kwargs):
        pass

    def estimate_minutes(self, _origin, _destination):
        return 7

    def fact_quality(self, _origin, _destination):
        return "EXPLICIT_FROZEN_FIXTURE"


def test_hard_live_capture_never_consults_even_an_explicit_mock_fallback(monkeypatch) -> None:
    monkeypatch.setattr(runtime, "settings", types.SimpleNamespace(live_valhalla_url="http://valhalla.test"))
    monkeypatch.setattr(runtime, "ValhallaHTTPMobilityProvider", _AlwaysFailLive)
    monkeypatch.setattr(runtime, "MockMobilityProvider", _ExplicitMockFallback)
    monkeypatch.setattr(runtime, "_place_lookup", lambda _session, _key: {"latitude": 0.0, "longitude": 0.0})
    with pytest.raises(MobilitySnapshotCaptureError):
        runtime.capture_runtime_mobility_snapshot(
            None,
            None,
            [("a", "b")],
            operation_key="mutation-hard-live",
            require_explicit_facts=True,
        )
