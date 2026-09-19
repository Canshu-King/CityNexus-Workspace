"""Retune the two appended guard tests against what the database and gates allow.

Measured on the first run:

  * `activities.place_id` carries a foreign key, so a made-up place is rejected
    before any product code sees it - the orphan case has to use a real place that
    is simply not on the active plan;
  * swapping the committed place out of a proposed plan is caught by the
    feasibility gate (`LOCKED_COMMITMENT_LOST`) before the remap loop runs, so the
    remap's own fail-closed branch needs a case feasibility lets through: the same
    place, at a time the commitment does not anchor to.
"""

import io

PATH = "backend/tests/test_sol_concurrency_and_remap.py"
text = io.open(PATH, encoding="utf-8", newline="").read()

old_orphan = """    with SessionLocal() as session:
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
"""
new_orphan = """    with SessionLocal() as session:
        journey = session.get(Journey, journey_id)
        on_plan = {
            item.place_id
            for item in session.scalars(
                select(Activity).where(
                    Activity.plan_version_id == journey.active_plan_version_id
                )
            ).all()
        }
        # A real Place (the column is a foreign key) that the active plan does not
        # contain, at a time nothing else shares.
        foreign = session.scalar(
            select(Activity)
            .where(Activity.plan_version_id != journey.active_plan_version_id)
            .where(Activity.place_id.not_in(on_plan | {None}))
        )
        assert foreign is not None, "no off-plan place is available for the orphan case"
        foreign.start_at = "2026-11-11T11:11:00+08:00"
        foreign.end_at = "2026-11-11T12:11:00+08:00"
        commitment = session.scalar(
            select(Commitment).where(
                Commitment.journey_id == journey_id, Commitment.status == "ACTIVE"
            )
        )
        commitment.activity_id = foreign.id
        policy = json.loads(commitment.policy_json or "{}")
        policy["semantic_key"] = foreign.place_id
        policy["scheduled_start_at"] = foreign.start_at
        commitment.policy_json = json.dumps(policy)
        session.commit()
"""
assert old_orphan in text
text = text.replace(old_orphan, new_orphan, 1)

old_drop = """    with SessionLocal() as session:
        # The solver's child plan no longer contains the committed place: the
        # activity is there in form, but it is a different place at a different time.
        for item in session.scalars(
            select(Activity).where(Activity.plan_version_id == proposal["proposed_plan_version_id"])
        ).all():
            if item.place_id == "place-river-cruise":
                item.place_id = "place-city-park"
        session.commit()
"""
new_drop = """    with SessionLocal() as session:
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
"""
assert old_drop in text
text = text.replace(old_drop, new_drop, 1)

io.open(PATH, "w", encoding="utf-8", newline="").write(text)
print("guard tests retuned")
