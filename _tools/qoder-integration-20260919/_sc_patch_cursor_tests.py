"""Patch the cursor tests to use a real off-plan activity, not a made-up id.

Measured while writing this file: `journeys.current_activity_id` carries a
foreign key, so a random uuid is rejected by SQLite before the projection ever
sees it.  That is not the interesting case.  The case that reaches production is
a cursor naming a row that exists — on a plan this journey is no longer
executing — which satisfies the key and still leaves the execution position
unresolvable.
"""

import io

PATH = "backend/tests/test_sol_execution_cursor.py"
text = io.open(PATH, encoding="utf-8", newline="").read()

helper = '''

def _off_plan_activity_id(journey_id: str) -> str:
    """A real Activity row that is not on the active plan.

    The foreign key on `journeys.current_activity_id` means a made-up id cannot
    be persisted at all, so it cannot be the test.  A pointer into another plan
    of the same journey satisfies the key and is still stale for the plan being
    executed, which is exactly the state the guard has to survive.
    """
    candidates = client.post(
        f"/api/v1/journeys/{journey_id}/plans/generate", json={"candidate_count": 3}
    ).json()
    with SessionLocal() as session:
        journey = session.get(Journey, journey_id)
        assert journey is not None
        for plan in candidates:
            if plan["id"] == journey.active_plan_version_id:
                continue
            for item in plan["activities"]:
                return str(item["id"])
    raise AssertionError("no off-plan activity is available to act as a stale cursor")

'''

anchor = "\ndef _experience"
if anchor not in text:
    # insert right after _plan_rows' block, before the served projection helper
    anchor = "\ndef _served_projection"
assert anchor in text
text = text.replace(anchor, helper + anchor, 1)

replacements = [
    (
        """def test_unknown_cursor_fails_closed_and_invents_no_now_next_or_leg() -> None:
    journey_id, _ = _started_journey()
    ghost = str(uuid4())
    _set_cursor(journey_id, ghost)
""",
        """def test_cursor_naming_an_off_plan_activity_fails_closed_and_invents_nothing() -> None:
    journey_id, _ = _started_journey()
    _set_cursor(journey_id, _off_plan_activity_id(journey_id))
""",
    ),
    (
        """    journey_id, activities = _started_journey()
    _set_cursor(journey_id, str(uuid4()))

    plan = client.get""",
        """    journey_id, activities = _started_journey()
    _set_cursor(journey_id, _off_plan_activity_id(journey_id))

    plan = client.get""",
    ),
    (
        """    _set_cursor(journey_id, str(uuid4()))
    snapshot = client.get(""",
        """    _set_cursor(journey_id, _off_plan_activity_id(journey_id))
    snapshot = client.get(""",
    ),
    (
        '''        ("unknown", lambda acts, jid: _set_cursor(jid, str(uuid4()))),''',
        '''        (
            "off-plan cursor",
            lambda acts, jid: _set_cursor(jid, _off_plan_activity_id(jid)),
        ),''',
    ),
]
for old, new in replacements:
    assert old in text, old[:60]
    text = text.replace(old, new, 1)

io.open(PATH, "w", encoding="utf-8", newline="").write(text)
print("cursor tests patched")
