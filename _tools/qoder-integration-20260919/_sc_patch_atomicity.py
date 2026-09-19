"""Put the plan transition under database authority instead of lock faith.

The pass-16 arbitration ruled that a process-local lock may be a second line of
defence but cannot be the sole closure basis for the acceptance races: two
backend processes would each hold their own lock and both would happily switch
plans.  This patch makes the durable layer decide:

  * `ux_plan_versions_single_active` (partial unique index) makes a second ACTIVE
    PlanVersion for one Journey impossible in the database itself;
  * the two status flips become conditional UPDATEs, so a writer whose base plan
    has already been replaced, or whose candidate has already been consumed, is
    rejected by the row count rather than by a read that raced it;
  * an IntegrityError at commit is translated into the same 409 conflict the
    optimistic checks produce, after a rollback, so nothing half-applied survives;
  * `locked_commitments_preserved` is re-derived from the commitment rows that
    exist *now*, immediately before the switch, instead of trusting the verdict
    computed when the proposal was generated.
"""

import io

PATH = "backend/app/main.py"
text = io.open(PATH, encoding="utf-8", newline="").read()

# ---------------------------------------------------------------- acceptance
old_switch = '''    decided_at = datetime.now(timezone.utc).isoformat()
    base.status = "SUPERSEDED"
    proposed.status = "ACTIVE"
    journey.active_plan_version_id = proposed.id
    journey.current_activity_id = replacement_current.id if replacement_current else None
    proposal.status = "ACCEPTED"
    proposal.decided_at = decided_at'''
new_switch = '''    decided_at = datetime.now(timezone.utc).isoformat()

    # Re-derive the commitment guard from the rows that exist *now*.  The stored
    # verdict was computed when the proposal was generated, and a booking can have
    # been captured in between - which is precisely how a stale `true` could author
    # a plan transition that destroys a promise made after the proposal was built.
    _revalidate_locked_commitments(session, journey, proposal, proposed)

    # Conditional writes, not object assignment.  A read-then-write of the ORM
    # rows is exactly the window two concurrent accepters can both pass; the
    # predicate below is evaluated by the database against the current row, so a
    # writer whose base plan has already been superseded, or whose candidate has
    # already been consumed, loses on rowcount rather than on a race it cannot see.
    _switch_active_plan_atomically(session, base=base, proposed=proposed, decided_at=decided_at)
    journey.active_plan_version_id = proposed.id
    journey.current_activity_id = replacement_current.id if replacement_current else None
    proposal.status = "ACCEPTED"
    proposal.decided_at = decided_at'''
assert old_switch in text, "acceptance switch anchor moved"
text = text.replace(old_switch, new_switch, 1)

# ---------------------------------------------------------------- commit guard
old_commit = '''            expires_at=(datetime.now(timezone.utc) + timedelta(days=7)).isoformat(),
        )
    )
    session.commit()
    return response


@app.post("/api/v1/replans/{proposal_id}/reject", response_model=ReplanProposalSchema)'''
new_commit = '''            expires_at=(datetime.now(timezone.utc) + timedelta(days=7)).isoformat(),
        )
    )
    try:
        session.commit()
    except IntegrityError as exc:
        # `ux_plan_versions_single_active` refused a second ACTIVE plan for this
        # Journey.  That is a concurrent acceptance from another session or
        # another process, i.e. a conflict with the same meaning as the optimistic
        # checks above - not a crash, and nothing may survive the rollback.
        session.rollback()
        raise HTTPException(
            409, "replan conflicts with an authoritative plan transition in progress"
        ) from exc
    return response


@app.post("/api/v1/replans/{proposal_id}/reject", response_model=ReplanProposalSchema)'''
assert old_commit in text, "acceptance commit anchor moved"
text = text.replace(old_commit, new_commit, 1)

# ---------------------------------------------------------------- helpers
anchor = '''def _accept_replan_impl(
    proposal_id: UUID,'''
helpers = '''def _switch_active_plan_atomically(
    session: Session, *, base: PlanVersion, proposed: PlanVersion, decided_at: str
) -> None:
    """Move the ACTIVE marker with predicates the database evaluates itself.

    Both flips are conditional.  The partial unique index
    `ux_plan_versions_single_active` then makes "two ACTIVE plans for one Journey"
    unrepresentable even if a future caller forgets this helper, and the commit
    path turns the resulting IntegrityError into the same 409 as everything else
    here.  A process-local lock cannot promise any of that across processes.
    """

    superseded = session.execute(
        update(PlanVersion)
        .where(PlanVersion.id == base.id, PlanVersion.status == "ACTIVE")
        .values(status="SUPERSEDED", updated_at=decided_at)
    )
    if superseded.rowcount != 1:
        session.rollback()
        raise HTTPException(409, "replan base plan is no longer the active plan")
    activated = session.execute(
        update(PlanVersion)
        .where(PlanVersion.id == proposed.id, PlanVersion.status == "CANDIDATE")
        .values(status="ACTIVE", updated_at=decided_at)
    )
    if activated.rowcount != 1:
        session.rollback()
        raise HTTPException(409, "replan candidate plan is no longer acceptable")
    # The bulk updates bypass the identity map, so every later read of these rows
    # in this transaction must come back from the database.
    session.expire_all()


def _revalidate_locked_commitments(
    session: Session, journey: Journey, proposal, proposed: PlanVersion
) -> None:
    """Recompute `locked_commitments_preserved` against current commitment truth.

    The field is a derived guard assertion, not a source of truth: the facts are
    the Commitment rows, the booking/payment state, and the activity identities on
    the canonical plans.  Recomputing it here closes the window where a payment was
    captured after the proposal was generated, because a boolean minted a minute
    ago cannot license destroying a promise made since.
    """

    locked_activity_ids = {
        item.id
        for item in session.scalars(
            select(Activity).where(
                Activity.plan_version_id == journey.active_plan_version_id,
                Activity.locked.is_(True),
            )
        ).all()
    }
    protected_activity_ids = {
        item.activity_id
        for item in session.scalars(
            select(CommitmentModel).where(
                CommitmentModel.journey_id == journey.id,
                CommitmentModel.status == "ACTIVE",
                CommitmentModel.level == "C4_Anchored",
                CommitmentModel.activity_id.is_not(None),
            )
        ).all()
    }
    must_survive = locked_activity_ids | protected_activity_ids
    if not must_survive:
        proposal.locked_commitments_preserved = True
        return
    child = {
        item.id: item
        for item in session.scalars(
            select(Activity).where(Activity.plan_version_id == proposed.id)
        ).all()
    }
    preserved = True
    for activity_id in must_survive:
        source = session.get(Activity, activity_id)
        if source is None:
            preserved = False
            break
        try:
            resolve_commitment_target(
                policy={
                    "semantic_key": str(source.place_id or source.city_service_id or ""),
                    "scheduled_start_at": source.start_at,
                },
                anchored_activity=source,
                candidates=list(child.values()),
                subject="locked commitment",
            )
        except CommitmentRemapConflict:
            preserved = False
            break
    proposal.locked_commitments_preserved = preserved
    if not preserved:
        raise HTTPException(
            409,
            "replan no longer preserves the locked and protected commitments captured "
            "since this proposal was generated",
        )


''' + anchor
assert anchor in text, "acceptance helper anchor moved"
text = text.replace(anchor, helpers, 1)

io.open(PATH, "w", encoding="utf-8", newline="").write(text)
print("acceptance is now database-backed")
