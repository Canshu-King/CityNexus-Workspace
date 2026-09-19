"""Record what the ambiguity probe actually measured instead of forcing a claim.

Two attempts to reach the acceptance remap's conflict branch through the public
endpoint both got intercepted earlier by the feasibility gate:

  * moving the committed activity's instant  -> LOCKED_COMMITMENT_LOST
  * duplicating the committed activity       -> ACTIVITY_OVERLAP + a duplicate-route
    mobility refusal

That is a finding, not a failure: a plan that could produce an ambiguous C4
anchor is already infeasible, so the remap's conflict branch is unreachable via
HTTP and is retained as defence in depth.  The test therefore asserts the
invariant the ruling cares about - acceptance refuses, nothing changes - and the
0 / 1 / many counting itself is covered directly against the resolver.
"""

import io

PATH = "backend/tests/test_sol_concurrency_and_remap.py"
text = io.open(PATH, encoding="utf-8", newline="").read()

old_doc = '''def test_accepting_a_recovery_with_an_ambiguous_c4_anchor_fails_closed() -> None:
    """Two candidate activities for one protected commitment: refuse, do not pick.

    The place and the instant both survive, so the feasibility gate is satisfied -
    this is the state that reaches the acceptance's own remap.  Choosing whichever
    row came first would invent an identity the record does not carry and strand
    the traveller's promise on an arbitrary activity.
    """'''
new_doc = '''def test_a_recovery_cannot_be_accepted_over_a_duplicated_protected_anchor() -> None:
    """Two activities claiming one protected commitment must never be accepted.

    Measured, and reported rather than smoothed over: this state is caught by the
    feasibility gate (`ACTIVITY_OVERLAP`) before the acceptance's own remap runs,
    and the sibling case - the committed activity moved to a different instant -
    is caught there too (`LOCKED_COMMITMENT_LOST`).  So the remap's conflict branch
    is not reachable through this endpoint; it stays as defence in depth, and the
    0 / 1 / many counting it depends on is asserted directly against the resolver
    in the three `resolve_commitment_target` tests below.  What this case does pin
    is the invariant the ruling asks for: the acceptance refuses, the Journey keeps
    exactly one ACTIVE plan, and the promise is not re-pointed at anything.
    """'''
assert old_doc in text
text = text.replace(old_doc, new_doc, 1)

old_assert = '''    assert "AMBIGUOUS" in accepted.text, (
        "the refusal did not come from the remap's ambiguity guard, so this test is "
        f"not exercising what it claims to: {accepted.text[:240]}"
    )'''
new_assert = '''    assert "place-river-cruise" in accepted.text, (
        "the refusal does not name the protected place at issue, so a traveller "
        f"cannot tell what was preserved: {accepted.text[:240]}"
    )'''
assert old_assert in text
text = text.replace(old_assert, new_assert, 1)

io.open(PATH, "w", encoding="utf-8", newline="").write(text)
print("ambiguity probe rewritten")
