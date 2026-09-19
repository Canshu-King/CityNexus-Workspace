"""Copy every column when cloning an activity, instead of naming a subset.

The hand-written constructor missed NOT NULL columns the model owns
(`travel_from_prev_min`, `estimated_cost_minor`, `currency`), so the clone was
rejected by SQLite before the product could be tested.
"""

import io

PATH = "backend/tests/test_sol_concurrency_and_remap.py"
text = io.open(PATH, encoding="utf-8", newline="").read()

old = """        twin = Activity(
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
        session.commit()"""
new = """        rows = session.scalars(
            select(Activity).where(
                Activity.plan_version_id == proposal["proposed_plan_version_id"]
            )
        ).all()
        columns = {
            column.name: getattr(original, column.name)
            for column in Activity.__table__.columns
            if column.name not in {"id", "plan_version_id", "sequence_no"}
        }
        twin = Activity(
            id=str(uuid4()),
            plan_version_id=original.plan_version_id,
            sequence_no=max(item.sequence_no for item in rows) + 40,
            **columns,
        )
        session.add(twin)
        session.commit()
        assert (
            session.scalar(
                select(func.count())
                .select_from(Activity)
                .where(
                    Activity.plan_version_id == original.plan_version_id,
                    Activity.place_id == "place-river-cruise",
                )
            )
            == 2
        ), "the duplicate anchor was not persisted, so this is not the ambiguity case"
"""
assert old in text
text = text.replace(old, new, 1)
text = text.replace(
    "from sqlalchemy import select",
    "from sqlalchemy import func, select",
    1,
)
io.open(PATH, "w", encoding="utf-8", newline="").write(text)
print("clone fixed")
