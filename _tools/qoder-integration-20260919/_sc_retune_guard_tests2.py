"""Make the C4 fail-closed branch reachable, and the orphan case deterministic.

Two things the previous attempt learned:

  * moving a committed activity's time is caught by the feasibility gate
    (`LOCKED_COMMITMENT_LOST`) long before the acceptance remap runs, so that
    route cannot exercise the remap's own conflict branch;
  * `activities.place_id` is a foreign key, so an invented place is rejected by
    SQLite before any product code sees it.

What does reach the remap branch is an *ambiguous* anchor: the place and the
instant both survive, so feasibility is satisfied, but two activities on the
proposed plan claim them.  Choosing one would invent an identity, so acceptance
has to refuse.
"""

import io

PATH = "backend/tests/test_sol_concurrency_and_remap.py"
text = io.open(PATH, encoding="utf-8", newline="").read()

old_orphan_head = """        # A real Place (the column is a foreign key) that the active plan does not
        # contain, at a time nothing else shares.
        foreign = session.scalar(
            select(Activity)
            .where(Activity.plan_version_id != journey.active_plan_version_id)
            .where(Activity.place_id.not_in(on_plan | {None}))
        )
        assert foreign is not None, "no off-plan place is available for the orphan case"
        foreign.start_at = "2026-11-11T11:11:00+08:00"
        foreign.end_at = "2026-11-11T12:11:00+08:00"
"""
new_orphan_head = """        # Any activity on another plan, moved to an instant no activity on the
        # active plan can share.  Identity plus scheduled instant both have to
        # match, so an unmatched instant is enough to make the anchor unresolvable
        # without inventing a Place the foreign key would reject.
        foreign = session.scalar(
            select(Activity)
            .where(Activity.plan_version_id != journey.active_plan_version_id)
            .where(Activity.place_id.is_not(None))
        )
        assert foreign is not None, "no off-plan activity is available for the orphan case"
        foreign.start_at = "2026-11-11T11:11:00+08:00"
        foreign.end_at = "2026-11-11T12:11:00+08:00"
"""
assert old_orphan_head in text
text = text.replace(old_orphan_head, new_orphan_head, 1)

old_drop = '''def test_accepting_a_recovery_that_cannot_honour_a_c4_fails_closed() -> None:
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
        # The place is still there, so the feasibility gate passes; what is missing
        # is the instant the commitment was anchored to.  This is the case the
        # remap's own fail-closed branch exists for - a plan that keeps the place
        # but not the promise attached to it.
        moved = False
        for item in session.scalars(
            select(Activity).where(Activity.plan_version_id == proposal["proposed_plan_version_id"])
        ).all():
            if item.place_id == "place-river-cruise":
                item.start_at = "2026-10-10T21:45:00+08:00"
                item.end_at = "2026-10-10T22:45:00+08:00"
                moved = True
        session.commit()
        assert moved, "the proposed plan never contained the committed place"
'''
new_drop = '''def test_accepting_a_recovery_with_an_ambiguous_c4_anchor_fails_closed() -> None:
    """Two candidate activities for one protected commitment: refuse, do not pick.

    The place and the instant both survive, so the feasibility gate is satisfied -
    this is the state that reaches the acceptance's own remap.  Choosing whichever
    row came first would invent an identity the record does not carry and strand
    the traveller's promise on an arbitrary activity.
    """
    journey_id, _cruise_activity, _booking = _journey_with_captured_commitment()
    proposal = _proposal_for(
        journey_id, _closed_activity_id(_plan_activities(journey_id)), "ambiguous-c4"
    )
    with SessionLocal() as session:
        original = next(
            item
            for item in session.scalars(
                select(Activity).where(
                    Activity.plan_version_id == proposal["proposed_plan_version_id"]
                )
            ).all()
            if item.place_id == "place-river-cruise"
        )
        twin = Activity(
            id=str(uuid4()),
            plan_version_id=original.plan_version_id,
            sequence_no=max(
                item.sequence_no
                for item in session.scalars(
                    select(Activity).where(
                        Activity.plan_version_id == proposal["proposed_plan_version_id"]
                    )
                ).all()
            )
            + 40,
            activity_type=original.activity_type,
            title=original.title,
            place_id=original.place_id,
            city_service_id=original.city_service_id,
            start_at=original.start_at,
            end_at=original.end_at,
            status=original.status,
            locked=original.locked,
            metadata_json=original.metadata_json,
        )
        session.add(twin)
        session.commit()
'''
assert old_drop in text
text = text.replace(old_drop, new_drop, 1)

old_assert = '''    assert accepted.status_code == 409, (
        "acceptance must refuse a plan that cannot carry the traveller's protected "
        f"commitment, got {accepted.status_code}: {accepted.text[:200]}"
    )
    assert "C4" in accepted.text, accepted.text[:200]'''
new_assert = '''    assert accepted.status_code == 409, (
        "acceptance must refuse a plan that cannot carry the traveller's protected "
        f"commitment unambiguously, got {accepted.status_code}: {accepted.text[:200]}"
    )
    assert "AMBIGUOUS" in accepted.text, (
        "the refusal did not come from the remap's ambiguity guard, so this test is "
        f"not exercising what it claims to: {accepted.text[:240]}"
    )'''
assert old_assert in text
text = text.replace(old_assert, new_assert, 1)

io.open(PATH, "w", encoding="utf-8", newline="").write(text)
print("guard tests retuned again")
