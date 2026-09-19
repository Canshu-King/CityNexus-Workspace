"""Append two convergence tests that the mutation check proved were missing.

Running the suite against four targeted sabotages showed two survivors:

  * removing the capture-side commitment re-anchor changed nothing, because the
    acceptance now re-points every active commitment before the capture can see a
    stale pointer - so the capture guard was untested defence in depth;
  * removing the C4 fail-closed branch changed nothing, because no test ever put
    a protected commitment into a proposed plan that could not honour it.

Both are added here as direct tests of the guard's own behaviour, independent of
how the bad state arose.
"""

import io

PATH = "backend/tests/test_sol_concurrency_and_remap.py"
text = io.open(PATH, encoding="utf-8", newline="").read()

addition = '''

# --------------------------------------------------------------------------
# the two guards the mutation check proved were untested
# --------------------------------------------------------------------------
def _move_commitment_pointer_off_plan(journey_id: str, *, place_id: str | None = None) -> str:
    """Point the journey's active commitment at an activity on another plan.

    The route does not matter; the guard has to hold whatever produced the state.
    """
    with SessionLocal() as session:
        journey = session.get(Journey, journey_id)
        candidates = list(
            session.scalars(
                select(Activity).where(Activity.plan_version_id != journey.active_plan_version_id)
            ).all()
        )
        if not candidates:
            raise AssertionError("no off-plan activity exists to simulate a stale pointer")
        target = candidates[0]
        if place_id is not None:
            target.place_id = place_id
        commitment = session.scalar(
            select(Commitment).where(
                Commitment.journey_id == journey_id, Commitment.status == "ACTIVE"
            )
        )
        commitment.activity_id = target.id
        session.commit()
        return target.id


def test_capture_reanchors_a_commitment_that_arrived_stale() -> None:
    """The capture must resolve the pointer before it promotes anything."""
    journey_id, _cruise, booking = _journey_with_uncaptured_booking()
    # A second plan exists after generation; park the pointer there.
    client.post(f"/api/v1/journeys/{journey_id}/plans/generate", json={"candidate_count": 1})
    _move_commitment_pointer_off_plan(journey_id, place_id="place-river-cruise")

    capture = client.post(
        f"/api/v1/journeys/{journey_id}/transactions",
        json={
            "booking_id": booking["id"],
            "transaction_type": "CAPTURE",
            "amount": booking["amount"],
        },
        headers={"Idempotency-Key": f"stale-capture-{booking['id']}"},
    )
    assert capture.status_code == 201, capture.text
    truth = _final_truth(journey_id)
    assert not truth["dangling_commitments"], (
        "the capture promoted a commitment whose pointer was outside the active plan"
    )
    assert not truth["off_plan_commitments"], truth["off_plan_commitments"]


def test_capture_refuses_when_no_active_activity_carries_the_commitment_identity() -> None:
    """Re-anchoring is not the same as inventing an anchor."""
    journey_id, _cruise, booking = _journey_with_uncaptured_booking()
    client.post(f"/api/v1/journeys/{journey_id}/plans/generate", json={"candidate_count": 1})
    # A pointer whose place exists nowhere on the active plan and whose scheduled
    # instant is moved: nothing may be bound to it.
    with SessionLocal() as session:
        journey = session.get(Journey, journey_id)
        foreign = session.scalar(
            select(Activity).where(Activity.plan_version_id != journey.active_plan_version_id)
        )
        foreign.place_id = "place-nowhere"
        foreign.start_at = "2026-11-11T11:11:00+08:00"
        foreign.end_at = "2026-11-11T12:11:00+08:00"
        commitment = session.scalar(
            select(Commitment).where(
                Commitment.journey_id == journey_id, Commitment.status == "ACTIVE"
            )
        )
        commitment.activity_id = foreign.id
        policy = json.loads(commitment.policy_json or "{}")
        policy["semantic_key"] = "place-nowhere"
        policy["scheduled_start_at"] = foreign.start_at
        commitment.policy_json = json.dumps(policy)
        session.commit()

    capture = client.post(
        f"/api/v1/journeys/{journey_id}/transactions",
        json={
            "booking_id": booking["id"],
            "transaction_type": "CAPTURE",
            "amount": booking["amount"],
        },
        headers={"Idempotency-Key": f"orphan-capture-{booking['id']}"},
    )
    assert capture.status_code == 409, (
        "a capture that cannot locate the commitment on the active plan must refuse, "
        f"not promote: {capture.status_code} {capture.text[:160]}"
    )
    truth = _final_truth(journey_id)
    assert not truth["dangling_commitments"], (
        "the refused capture still left a protected commitment stranded off-plan"
    )


def test_accepting_a_recovery_that_cannot_honour_a_c4_fails_closed() -> None:
    """A recovery that silently drops a protected place is worse than no recovery.

    Without the fail-closed branch the acceptance would commit, the C4 would keep
    pointing at the superseded plan, and the traveller would be told the promise
    was preserved.
    """
    journey_id, _cruise_activity, _booking = _journey_with_captured_commitment()
    proposal = _proposal_for(
        journey_id, _closed_activity_id(_plan_activities(journey_id)), "drop-c4"
    )
    with SessionLocal() as session:
        # The solver's child plan no longer contains the committed place: the
        # activity is there in form, but it is a different place at a different time.
        for item in session.scalars(
            select(Activity).where(Activity.plan_version_id == proposal["proposed_plan_version_id"])
        ).all():
            if item.place_id == "place-river-cruise":
                item.place_id = "place-city-park"
        session.commit()

    accepted = client.post(
        f"/api/v1/replans/{proposal['id']}/accept",
        headers={"Idempotency-Key": f"drop-c4-{proposal['id']}"},
    )
    assert accepted.status_code == 409, (
        "acceptance must refuse a plan that cannot carry the traveller's protected "
        f"commitment, got {accepted.status_code}: {accepted.text[:200]}"
    )
    assert "C4" in accepted.text, accepted.text[:200]
    truth = _final_truth(journey_id)
    assert len(truth["active_plan_ids"]) == 1
    assert truth["journey_plan_id"] == truth["active_plan_ids"][0]
    assert not truth["dangling_commitments"]
    assert proposal["id"] not in truth["accepted_proposal_ids"], (
        "the rejected acceptance still recorded the proposal as ACCEPTED"
    )
'''

marker = "\n\n# --------------------------------------------------------------------------\n# shared setup for the race tests"
assert marker in text
text = text.replace(marker, addition + marker, 1)
io.open(PATH, "w", encoding="utf-8", newline="").write(text)
print("guard tests appended")
