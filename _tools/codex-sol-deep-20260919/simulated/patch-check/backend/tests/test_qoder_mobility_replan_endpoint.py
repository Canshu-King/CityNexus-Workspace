"""T2 — REAL /replans endpoint path (API/service integration, B1).

The v1 tests for this contract only exercised ``MockMobilityProvider(strict=True)``
and the ``_replan_estimate`` primitive.  GPT's independent review (v2, B1) pointed
out that the real ``generate_replan`` builds a bulk ``mobility_pairs`` set for
replacement candidates and captures it *before* ``_replan_estimate`` runs, so a
missing leg could be frozen at the blanket ``default_minutes=20`` and then read
back as if it were measured — "back door locked, front door open."

These tests drive the actual ``POST /api/v1/journeys/{id}/replans`` endpoint with
a fixture in which a candidate's legs have no explicit fact (they would fall to
the synthetic default), and assert the endpoint refuses to base a hard
feasibility decision on that fabricated constant.

Layer label (docs/TEST_AND_EVIDENCE_GATE.md): API/service integration.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.integrations.mock import providers as providers_mod
from app.main import app

client = TestClient(app)

# Legs used by the golden same-slot replacement candidates when the tech-art
# venue closes and the plan must route food-hall -> {candidate} -> river-cruise.
_CANDIDATE_LEGS = (
    "place-food-hall|place-city-park",
    "place-city-park|place-river-cruise",
    "place-food-hall|place-design-library",
    "place-design-library|place-river-cruise",
)


@pytest.fixture()
def _strip_explicit_legs(monkeypatch):
    """Make named fixture pairs fall back to the blanket default (20).

    Only the DATA is altered (an explicit matrix entry is deleted); no product
    logic is patched, so the endpoint exercises its real capture + gate path.
    """

    def apply(pairs: tuple[str, ...]) -> None:
        original_init = providers_mod.MockMobilityProvider.__init__

        def patched_init(self, place_lookup=None, *, strict=False):
            original_init(self, place_lookup, strict=strict)
            for key in pairs:
                self._fixture["minutes"].pop(key, None)

        monkeypatch.setattr(
            providers_mod.MockMobilityProvider, "__init__", patched_init
        )

    return apply


def _drive_to_closure() -> tuple[str, str]:
    ids = client.post("/api/v1/demo/reset").json()
    jid = ids["journey_id"]
    generated = client.post(
        f"/api/v1/journeys/{jid}/plans/generate", json={"candidate_count": 1}
    )
    assert generated.status_code == 201, generated.text
    plan = generated.json()[0]
    assert client.post(f"/api/v1/journeys/{jid}/plans/{plan['id']}/select").status_code == 200
    tech = next(a for a in plan["activities"] if a["place_id"] == "place-tech-art")
    started = client.post(f"/api/v1/journeys/{jid}/start")
    assert started.status_code == 200, started.text
    # Advance execution to the disrupted activity's predecessor so the closure is
    # a live, mutable replan rather than a pre-start plumbing probe.
    for activity in plan["activities"]:
        if activity["id"] == tech["id"]:
            break
        client.post(f"/api/v1/journeys/{jid}/activities/{activity['id']}/complete")
    event = client.post(
        f"/api/v1/journeys/{jid}/events",
        json={
            "event_type": "CLOSURE",
            "severity": "MAJOR",
            "affected_activity_id": tech["id"],
            "occurred_at": "2026-10-10T13:25:00+08:00",
            "payload": {"reason": "t2 endpoint truth test"},
        },
    )
    assert event.status_code == 201, event.text
    return jid, event.json()["id"]


def test_replans_never_freezes_synthetic_default_as_hard_fact(_strip_explicit_legs) -> None:
    """Endpoint regression 1 + 6: a missing leg is not priced at 20 as truth.

    Control first: with the golden fixture intact the same closure yields a 201
    proposal, so we know the endpoint *can* recover here and the failure below is
    caused by the missing evidence, not by an unrelated broken setup.  Then every
    candidate leg is forced to fall back to the blanket default.  Before V2-T2
    the real ``generate_replan`` captured that default as a frozen ``20`` and fed
    it to the gate; the endpoint must now fail closed with
    ``MOBILITY_DATA_UNAVAILABLE`` instead.
    """

    # Control (fixture intact) -> a proposal is produced.
    ctl_jid, ctl_event = _drive_to_closure()
    control = client.post(
        f"/api/v1/journeys/{ctl_jid}/replans",
        json={"trigger_event_id": ctl_event, "candidate_count": 3},
    )
    assert control.status_code == 201, control.text

    # Now strip every candidate leg and re-drive the real endpoint.
    _strip_explicit_legs(_CANDIDATE_LEGS)
    jid, event_id = _drive_to_closure()
    response = client.post(
        f"/api/v1/journeys/{jid}/replans",
        json={"trigger_event_id": event_id, "candidate_count": 3},
    )
    assert response.status_code == 422, (
        "the endpoint returned a proposal instead of failing closed — a synthetic "
        f"default 20 likely reached hard feasibility: {response.text[:200]}"
    )
    assert "MOBILITY_DATA_UNAVAILABLE" in response.text, response.text


def test_v3_03_seed_helper_neutralises_b1_sentinel(monkeypatch) -> None:
    """V3-3 sentinel: only declared legs become hard-eligible; the rest stay missing.

    Proves the narrowed seed helper did NOT turn the whole demo world into
    "known mobility" — a pair outside the scenario table is still synthetic and
    therefore unavailable for hard feasibility.
    """

    from _qoder_explicit_demo_mobility import seed_explicit_mobility
    from app.integrations.mock.providers import MockMobilityProvider
    from app.replanning.provider_snapshots import EXPLICIT_FROZEN_FIXTURE, SYNTHETIC_DEFAULT

    seed_explicit_mobility(monkeypatch, {("place-food-hall", "place-city-park"): 14})
    provider = MockMobilityProvider()
    # Seeded, declared leg -> trustworthy explicit fact.
    assert provider.fact_quality("place-food-hall", "place-city-park") == EXPLICIT_FROZEN_FIXTURE
    # Undeclared pair -> still the refused blanket default, NOT laundered to known.
    assert provider.fact_quality("place-old-town", "place-skyline-dinner") == SYNTHETIC_DEFAULT


def test_replans_keeps_the_explicit_candidate_when_only_another_is_default(
    _strip_explicit_legs,
) -> None:
    """V3-2 deterministic candidate-specific proof: A survives, B is refused.

    city-park keeps its explicit fixture legs; ONLY design-library's legs are
    stripped so it falls back to the refused default.  The endpoint must return
    201 and offer the trustworthy city-park candidate — proving that one
    candidate's missing evidence does not abort the whole recovery.  (The old
    version accepted 422 as a pass, which proved nothing; this must be a 201.)
    """

    _strip_explicit_legs(
        ("place-food-hall|place-design-library", "place-design-library|place-river-cruise")
    )
    jid, event_id = _drive_to_closure()
    response = client.post(
        f"/api/v1/journeys/{jid}/replans",
        json={"trigger_event_id": event_id, "candidate_count": 3},
    )
    # Deterministic: the explicit candidate keeps recovery alive -> exactly 201.
    assert response.status_code == 201, response.text
    proposals = client.get(f"/api/v1/journeys/{jid}/replans").json()
    added = {str((p.get("diff") or {}).get("added")) for p in proposals}
    assert any("place-city-park" in a for a in added), (
        "the candidate with trustworthy mobility was wrongly dropped: " + str(added)
    )
    assert not any("place-design-library" in a for a in added), (
        "a candidate resting on refused synthetic-default mobility was offered: " + str(added)
    )
