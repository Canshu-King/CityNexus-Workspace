"""Append the cross-process proof the arbitration asked for.

The ruling was explicit: a process-local lock may be a second line of defence but
cannot be the sole basis for closing the acceptance races.  So these cases remove
the lock from the picture entirely - two independent sessions calling the
serialized implementation directly, which is what two backend processes would do -
and assert the database still refuses a second ACTIVE PlanVersion.
"""

import io

PATH = "backend/tests/test_sol_concurrency_and_remap.py"
text = io.open(PATH, encoding="utf-8", newline="").read()

addition = '''

# --------------------------------------------------------------------------
# the invariant must hold without the lock, because the lock is per-process
# --------------------------------------------------------------------------
def test_two_sessions_without_the_lock_still_cannot_produce_two_active_plans() -> None:
    """Simulate two backend processes: separate sessions, no shared guard.

    `journey_write_lock` only serializes inside one process, so a race that is
    closed by the lock alone is not closed.  Here the lock is bypassed entirely by
    calling the serialized implementation from two sessions at once.  The
    surviving guarantee has to be the database's: conditional writes plus
    `ux_plan_versions_single_active`.
    """
    from app.main import _accept_replan_serialized_impl

    journey_id, _ = _started_for_race()
    activities = _plan_activities(journey_id)
    first = _proposal_for(journey_id, _closed_activity_id(activities), "xproc-a")
    second = _proposal_for(journey_id, _closed_activity_id(activities), "xproc-b")
    assert first["base_plan_version_id"] == second["base_plan_version_id"]

    outcomes: list[str] = []
    barrier = threading.Barrier(2)

    def worker(proposal_id: str) -> None:
        from uuid import UUID as _UUID

        barrier.wait()
        with SessionLocal() as session:
            try:
                _accept_replan_serialized_impl(
                    _UUID(proposal_id),
                    f"xproc-{proposal_id}",
                    session,
                )
                outcome = "accepted"
            except Exception as exc:  # HTTPException from the conflict paths
                outcome = f"conflict:{getattr(exc, 'status_code', type(exc).__name__)}"
            finally:
                session.rollback()
                session.close()
        outcomes.append(outcome)

    threads = [threading.Thread(target=worker, args=(pid,)) for pid in (first["id"], second["id"])]
    for item in threads:
        item.start()
    for item in threads:
        item.join()

    truth = _final_truth(journey_id)
    assert len(truth["active_plan_ids"]) == 1, (
        "two sessions without the shared lock produced more than one ACTIVE plan, so "
        f"the invariant lived only inside one process: {truth['active_plan_ids']}"
    )
    assert truth["journey_plan_id"] == truth["active_plan_ids"][0]
    assert outcomes.count("accepted") == 1, outcomes
    assert all(item.startswith("conflict:409") for item in outcomes if item != "accepted"), outcomes
    assert not truth["dangling_commitments"], truth


def test_the_database_itself_refuses_a_second_active_plan() -> None:
    """The index, not the application, is the last word.

    A raw second ACTIVE row for one Journey is written through a separate session
    with no product code involved.  If that succeeds, every race conclusion in
    this file rests on a lock that does not exist across processes.
    """
    journey_id, _ = _started_for_race()
    with SessionLocal() as session:
        journey = session.get(Journey, journey_id)
        existing = session.scalar(
            select(PlanVersion).where(PlanVersion.id == journey.active_plan_version_id)
        )
        rival = PlanVersion(
            id=str(uuid4()),
            journey_id=journey_id,
            version_no=existing.version_no + 500,
            planning_mode=existing.planning_mode,
            status="ACTIVE",
            source=existing.source,
            currency=existing.currency,
        )
        session.add(rival)
        with pytest.raises(IntegrityError):
            session.commit()
        session.rollback()
        assert (
            session.scalar(
                select(func.count())
                .select_from(PlanVersion)
                .where(
                    PlanVersion.journey_id == journey_id, PlanVersion.status == "ACTIVE"
                )
            )
            == 1
        ), "the rejected write left a second ACTIVE plan behind anyway"
'''

marker = "\n\n# --------------------------------------------------------------------------\n# shared setup for the race tests"
assert marker in text
text = text.replace(marker, addition + marker, 1)
text = text.replace(
    "from sqlalchemy import func, select",
    "from sqlalchemy import func, select\nfrom sqlalchemy.exc import IntegrityError",
    1,
)
io.open(PATH, "w", encoding="utf-8", newline="").write(text)
print("cross-process cases appended")
