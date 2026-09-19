from __future__ import annotations

import gc
import json
from types import SimpleNamespace

import pytest

from app import concurrency_guards
from app.commerce.service_impl import CommerceConflict, _remap_commitment_to_active_plan
from app.db.models import Activity, Journey


START = "2026-10-09T10:00:00+08:00"


class _Scalars:
    def __init__(self, rows: list[object]) -> None:
        self.rows = rows

    def all(self) -> list[object]:
        return self.rows


class _Session:
    def __init__(self, journey: object, current: object, candidates: list[object]) -> None:
        self.journey = journey
        self.current = current
        self.candidates = candidates

    def get(self, model: object, key: str) -> object | None:
        if model is Journey and key == self.journey.id:
            return self.journey
        if model is Activity and key == self.current.id:
            return self.current
        return None

    def scalars(self, _statement: object) -> _Scalars:
        return _Scalars(self.candidates)


def _activity(
    activity_id: str,
    plan_id: str,
    *,
    semantic: str | None,
    place: str = "place-shared",
    start: str = START,
) -> object:
    metadata = {"semantic_node_key": semantic} if semantic else {}
    return SimpleNamespace(
        id=activity_id,
        plan_version_id=plan_id,
        place_id=place,
        city_service_id=None,
        start_at=start,
        end_at="2026-10-09T11:00:00+08:00",
        metadata_json=json.dumps(metadata),
    )


def _fixture(candidates: list[object]) -> tuple[_Session, object]:
    journey = SimpleNamespace(id="journey", active_plan_version_id="active")
    current = _activity("old", "superseded", semantic="node:cruise")
    commitment = SimpleNamespace(
        journey_id=journey.id,
        activity_id=current.id,
        policy_json=json.dumps(
            {"semantic_node_key": "node:cruise", "scheduled_start_at": START}
        ),
    )
    return _Session(journey, current, candidates), commitment


def test_unique_exact_semantic_identity_remaps_to_current_active_plan() -> None:
    candidate = _activity("new", "active", semantic="node:cruise")
    session, commitment = _fixture([candidate])

    _remap_commitment_to_active_plan(session, commitment)

    assert commitment.activity_id == candidate.id
    assert candidate.plan_version_id == session.journey.active_plan_version_id


def test_no_equivalent_activity_fails_closed() -> None:
    session, commitment = _fixture(
        [_activity("different", "active", semantic="node:museum", place="other")]
    )
    with pytest.raises(CommerceConflict, match="cannot be attached"):
        _remap_commitment_to_active_plan(session, commitment)
    assert commitment.activity_id == "old"


def test_same_place_and_time_but_different_semantics_do_not_remap() -> None:
    session, commitment = _fixture(
        [
            _activity("museum", "active", semantic="node:museum"),
            _activity("dinner", "active", semantic="node:dinner"),
        ]
    )
    with pytest.raises(CommerceConflict, match="cannot be attached"):
        _remap_commitment_to_active_plan(session, commitment)
    assert commitment.activity_id == "old"


def test_two_semantically_matching_candidates_fail_closed_as_ambiguous() -> None:
    session, commitment = _fixture(
        [
            _activity("new-a", "active", semantic="node:cruise"),
            _activity("new-b", "active", semantic="node:cruise"),
        ]
    )
    with pytest.raises(CommerceConflict, match="AMBIGUOUS"):
        _remap_commitment_to_active_plan(session, commitment)
    assert commitment.activity_id == "old"


def test_process_local_lock_registry_releases_unused_journey_keys() -> None:
    assert concurrency_guards.PROCESS_LOCAL_ONLY is True
    key = "closeout-ephemeral-journey"
    with concurrency_guards.journey_write_lock(key):
        assert key in concurrency_guards._journey_locks
    gc.collect()
    assert key not in concurrency_guards._journey_locks
