# Commitment-Centric Recovery Evidence

## Mid-trip C4 path

The V13 test imports a structured reservation through the real Journey Inbox
API with `anchor_role=MID_TRIP`, a scheduled arrival, a semantic node key, a
known price and currency. Confirmation creates a `C4_Anchored` Commitment with
the semantic key and arrival anchor. Authoritative compose then binds that
commitment to the selected Activity rather than treating it as an unrelated
booking.

Evidence:

- `backend/tests/test_v13_integrity.py::test_v13_mid_trip_c4_is_fixed_and_bound_to_selected_activity_via_inbox_api`
- `backend/app/operations/v9.py` reservation normalization and canonical
  semantic-node mapping
- `backend/app/planning/authoritative_v12.py` mid-trip anchor feasibility

Impossible anchors are deterministic conflicts, not silent relaxations:

- an arrival outside the Journey window returns `V13_COMMITMENT_ANCHOR`;
- a semantic key not present in the input returns
  `V13_C4_ANCHOR_NOT_IN_INPUT`.

## Recovery protection

The Golden recovery configures an autonomous envelope with a zero automatic
loss limit, bounded cost/schedule drift, no automatic commitment management,
and protected `C4_Anchored` levels. A provider/replay risk event is allowed to
replace a reversible future activity. The recovery creates a new active
PlanVersion while the protected Commitment remains `ACTIVE` and bound to its
selected Activity. Attempting to skip the protected current activity returns
`PROTECTED_COMMITMENT_CANNOT_BE_SKIPPED` without advancing the Journey.

This demonstrates the intended policy boundary: C4 is not an absolute
AI-ban, but durable commitment mutation requires explicit higher policy and
the provider/loss/authorization facts required by that policy. The V13 Golden
does not grant that higher policy, so it protects the anchor and autonomously
changes only the reversible portion.
