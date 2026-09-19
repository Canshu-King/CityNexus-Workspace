"""Hypothesis state machine that drives real CityNexus APIs and persistence."""
from __future__ import annotations

import json
import sys
from pathlib import Path
from uuid import uuid4

from fastapi.testclient import TestClient
from hypothesis import HealthCheck, settings, strategies as st
from hypothesis.stateful import Bundle, RuleBasedStateMachine, initialize, invariant, rule
from sqlalchemy import select

BACKEND_TESTS = Path(__file__).resolve().parents[1] / "snapshot" / "citynexus" / "backend" / "tests"
sys.path.insert(0, str(BACKEND_TESTS))

from app.db.models import Activity, Commitment, Event, Journey, PlanVersion, ReplanProposal  # noqa: E402
from app.db.session import SessionLocal  # noqa: E402
from app.integrations.mock import providers as mock_providers  # noqa: E402
from app.main import app  # noqa: E402


# Scenario-declared explicit fact used by the real replan path. Unknown pairs
# remain synthetic and are still rejected by hard feasibility.
_original_init = mock_providers.MockMobilityProvider.__init__


def _patched_init(self, place_lookup=None, *, strict=False):
    _original_init(self, place_lookup, strict=strict)
    self._fixture["minutes"].setdefault("place-food-hall|place-river-cruise", 20)


mock_providers.MockMobilityProvider.__init__ = _patched_init


class RealCityNexusMachine(RuleBasedStateMachine):
    events = Bundle("events")
    proposals = Bundle("proposals")

    def __init__(self) -> None:
        super().__init__()
        self.client = TestClient(app)
        self.journey_id = ""
        self.initial_plan_id = ""
        self.accepted_response_by_key: dict[str, dict] = {}

    @initialize()
    def setup_real_journey(self) -> None:
        ids = self.client.post("/api/v1/demo/reset").json()
        self.journey_id = ids["journey_id"]
        generated = self.client.post(
            f"/api/v1/journeys/{self.journey_id}/plans/generate", json={"candidate_count": 1}
        )
        assert generated.status_code == 201, generated.text
        plan = generated.json()[0]
        self.initial_plan_id = plan["id"]
        assert self.client.post(
            f"/api/v1/journeys/{self.journey_id}/plans/{plan['id']}/select"
        ).status_code == 200
        assert self.client.post(f"/api/v1/journeys/{self.journey_id}/start").status_code == 200

    @rule(target=events, delay=st.integers(min_value=1, max_value=90))
    def detect_disruption(self, delay: int) -> str:
        response = self.client.post(
            f"/api/v1/journeys/{self.journey_id}/events",
            json={"event_type": "SCHEDULE_DELAY", "payload": {"delay_minutes": delay}},
        )
        assert response.status_code == 201, response.text
        return response.json()["id"]

    @rule(target=proposals, event_id=events)
    def generate_replan(self, event_id: str) -> str:
        response = self.client.post(
            f"/api/v1/journeys/{self.journey_id}/replans",
            json={"trigger_event_id": event_id, "candidate_count": 1},
        )
        assert response.status_code in {201, 409, 422}, response.text
        return response.json()["id"] if response.status_code == 201 else f"rejected:{event_id}"

    @rule(proposal_id=proposals, key_seed=st.integers(min_value=0, max_value=5))
    def accept_or_retry(self, proposal_id: str, key_seed: int) -> None:
        if proposal_id.startswith("rejected:"):
            return
        key = f"stateful-accept-{proposal_id}-{key_seed}"
        response = self.client.post(
            f"/api/v1/replans/{proposal_id}/accept", headers={"Idempotency-Key": key}
        )
        assert response.status_code in {200, 409}, response.text
        if response.status_code == 200:
            body = response.json()
            if key in self.accepted_response_by_key:
                assert body == self.accepted_response_by_key[key]
            self.accepted_response_by_key[key] = body

    @rule(proposal_id=proposals)
    def reject(self, proposal_id: str) -> None:
        if proposal_id.startswith("rejected:"):
            return
        response = self.client.post(f"/api/v1/replans/{proposal_id}/reject")
        assert response.status_code in {200, 409}, response.text

    @rule()
    def read_all_authoritative_projections(self) -> None:
        for suffix in ("", "/experience", "/twin", "/offline-snapshot", "/execution-clock", "/replans"):
            response = self.client.get(f"/api/v1/journeys/{self.journey_id}{suffix}")
            assert response.status_code == 200, (suffix, response.text)

    @rule()
    def advance_current_activity(self) -> None:
        twin = self.client.get(f"/api/v1/journeys/{self.journey_id}/twin").json()
        execution = twin["context"]["execution"]
        activity_id = execution.get("now_activity_id")
        state = execution.get("now_state")
        action = {"ACTIVE": "depart", "EN_ROUTE": "arrive", "ARRIVED": "begin", "IN_PROGRESS": "complete"}.get(state)
        if activity_id and action:
            response = self.client.post(
                f"/api/v1/journeys/{self.journey_id}/activities/{activity_id}/{action}"
            )
            assert response.status_code == 200, response.text

    @rule()
    def duplicate_booking_attempt(self) -> None:
        experience = self.client.get(f"/api/v1/journeys/{self.journey_id}/experience").json()
        activities = (experience.get("active_plan") or {}).get("activities") or []
        if not activities:
            return
        response = self.client.post(
            f"/api/v1/journeys/{self.journey_id}/bookings", json={"activity_id": activities[-1]["id"]}
        )
        assert response.status_code in {201, 409, 422}, response.text

    @invariant()
    def persisted_state_is_coherent(self) -> None:
        with SessionLocal() as session:
            journey = session.get(Journey, self.journey_id)
            assert journey is not None
            active = session.scalars(
                select(PlanVersion).where(
                    PlanVersion.journey_id == self.journey_id, PlanVersion.status == "ACTIVE"
                )
            ).all()
            assert len(active) == 1
            assert journey.active_plan_version_id == active[0].id
            if journey.current_activity_id is not None:
                current = session.get(Activity, journey.current_activity_id)
                assert current is not None
                assert current.plan_version_id == active[0].id
            accepted = session.scalars(
                select(ReplanProposal).where(
                    ReplanProposal.journey_id == self.journey_id,
                    ReplanProposal.status == "ACCEPTED",
                )
            ).all()
            triggers = [item.trigger_event_id for item in accepted]
            assert len(triggers) == len(set(triggers))
            for item in accepted:
                assert item.trigger_event_id
                event = session.get(Event, item.trigger_event_id)
                assert event is not None and event.journey_id == self.journey_id
                diff = json.loads(item.diff_json or "{}")
                assert diff.get("candidate_family") or diff.get("added") or diff.get("removed") or diff.get("moved")
            for commitment in session.scalars(
                select(Commitment).where(
                    Commitment.journey_id == self.journey_id,
                    Commitment.status == "ACTIVE",
                    Commitment.level == "C4_Anchored",
                )
            ).all():
                if commitment.activity_id:
                    activity = session.get(Activity, commitment.activity_id)
                    assert activity is not None
                    assert activity.plan_version_id == active[0].id


TestRealCityNexusMachine = RealCityNexusMachine.TestCase
TestRealCityNexusMachine.settings = settings(
    max_examples=60,
    stateful_step_count=30,
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow],
)
