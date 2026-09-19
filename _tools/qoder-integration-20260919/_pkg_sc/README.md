# Qoder — Sol Truth Convergence Integration

Executes sections A-H of the Sol handoff against the current Qoder line, and
packages the result for external GPT arbitration as section K requires.

## Baseline, stated up front

The handoff names `0af1905` as the current line.  This work sits on `fec2204`
(the delivered pass-16 HEAD) instead, and deliberately so: the four Sol defects
were located in code the pass-16 commits never touched (cursor parsing, replan
acceptance, payment capture, serialization), and reverting would drop two items
the GPT arbitration had already ordered fixed and that have since been delivered
for review.  No Sol commit was fetched or cherry-picked; `c19daa54` and
`776be4e9` are unreadable in both repositories this line lives in and were used
only as behaviour references, read out of the verification snapshot.

## Changed files

| commit | files |
|---|---|
| `fed2311` | `app/concurrency_guards.py` (new), `app/replanning/commitment_remap.py` (new), `app/main.py`, `app/operations/v9.py`, `app/commerce/service_impl.py`, `app/stay_mobility.py` |
| `5951beb` | `src/app/V8Experience.tsx`, `src/app/v8Types.ts`, `src/i18n/LocaleContext.tsx` |
| `79d2098` | `tests/test_sol_execution_cursor.py`, `tests/test_sol_concurrency_and_remap.py`, `e2e/qoder-stale-cursor.spec.ts` |

`COMMITS.txt` prints the real file list for the gates tree.

## A / CX-SOL-001 — the cursor is an assertion, not a hint

`_execution_truth` had one branch for "cursor absent" and "cursor unresolvable",
and it fell back to the first pending activity.  Now three states: `VALID`
projects exactly that activity, `ABSENT_FALLBACK` may project the first
non-terminal step because that is the truth before anything has happened, and
`STALE` projects no Now, no Next and no NextLeg.  `cursor_status` is carried by
every projection - offline snapshot, Edge journey-snapshot, `/experience` - so
the absence of authoritative execution truth is observable rather than rendered
as something plausible.  The Edge surface used to say "Journey complete" for a
stale cursor; it now says the position is unresolved.

Measured while writing the tests, and it changed them: `current_activity_id` and
`activities.place_id` are foreign keys, so a fabricated id cannot be persisted
at all.  The realistic stale shape is a pointer to a real activity on another
plan, which satisfies the key and is still unresolvable.

The frontend read `activities[0]`/`activities[1]`/`legs[0]` and never consulted
the cursor.  Both Live surfaces now share one resolver mirroring the backend
table, and a stale cursor says "Execution position unresolved" instead of
"Awaiting plan" - the latter sent the traveller to fix a problem that is not
theirs.  `/experience` activities gained `status`, without which a client can
only infer "done" from order.

## B — Journey-scoped serialization, and what it is not

`journey_write_lock(journey_id)` wraps the complete read/validate/mutate/commit
transition for replan acceptance, the payment-transaction endpoint, and the
commitment promotion inside them - taken before the first read, released after
the commit, with the identity map expired on entry because the lookup that chose
the lock key happened outside it.

`PROCESS_LOCAL_ONLY = True` is stated as a constant, in the module docstring and
in the call-site comments: it is not multi-worker safe and not distributed safe,
the reference deployment is one process on SQLite, and SQLite does not honour
`SELECT ... FOR UPDATE`, so there is no database backstop behind it.  Swapping in
a database or advisory lock changes one function and no business invariant.

## C/D — races assert final canonical truth

`_final_truth()` reads rows, not endpoints: the ACTIVE PlanVersion set, what the
Journey points at, the ACCEPTED proposal set and the plan each names, any active
commitment anchored outside the active plan, and whether the cursor still
resolves.  Four deterministic schedules (barrier-released, no sleeps as
correctness): same proposal against itself with different keys, the same
idempotency key concurrently, competing proposals on one base plan, and
acceptance against capture.  The losing competitor lands in the existing
`INVALIDATED` state - no status was invented for a test.

## E / CX-EXT-004 — a capture may no longer promote a stale pointer

The capture path never read the Journey, the active plan, or feasibility; it
promoted whatever `Commitment.activity_id` pointed at.  It now resolves the
anchor first and fails closed when the active plan cannot carry it.  Acceptance
also re-points every active commitment rather than only C4s: an unresolvable C4
refuses the whole acceptance, an unresolvable ordinary booking is skipped rather
than blocking a recovery the traveller needs.

## F — one counting rule for all three re-pointing sites

Zero matches fails closed, exactly one rebinds, more than one is AMBIGUOUS and
fails closed - in one module, used by acceptance, capture and authoritative plan
activation.  Two approximations were removed: `candidate.endswith(term)` inside
acceptance (string similarity posing as identity, where a short key claims any
longer one sharing its suffix), and the activation path's silent
`by_semantic.get(...) or by_place.get(...)`, which stranded a commitment on the
replaced plan and let a later row overwrite an earlier one.  Activation now
raises.  Identity is exact-equality on semantic keys and place/service ids plus
the anchored instant; titles are never consulted.

Sol's physical-identity implementation was not ported.  `compare_physical_venue`,
`HARD_FEASIBLE_QUALITIES`, mobility provenance and the fact-quality rules are
untouched, as section F requires.

## G/H — how the tests were made strong enough to keep

`tools/sc_mutation_check.py` applies eight targeted sabotages one at a time, runs
the convergence suite, and restores every file; its log ships as
`runs/mutation_check.log`.  Result: **7 killed, 1 survived**.  The survivor is the
acceptance remap's own conflict branch, and the reason is measured rather than
assumed - deleting the committed activity trips `LOCKED_COMMITMENT_LOST` and
duplicating it trips `ACTIVITY_OVERLAP`, both inside the feasibility gate, so no
public route reaches that branch.  It stays as defence in depth and its counting
is asserted directly against the resolver.  The kill list is reproducible from
the shipped script.

The mutation check also caught a vacuous test of my own: the first
capture-versus-accept race re-captured an already-captured booking, so the second
caller could only answer 409 and no commitment could ever strand - it stayed
green with the lock deleted.  It now uses an uncaptured booking, which is the
state that can actually strand a promise.

The projection oracle recomputes the window straight from the Activity and
JourneyLeg rows and compares `cursor_status`, `now_activity_id`,
`next_activity_id`, `next_leg_id`, `next_mode` and `next_eta_min` across five
cursor states and after an accepted replan.  `next_leg_id` was added to the
payload for this: two legs can share a mode and a duration and still be different
promises.

## Numbers (one authoritative run, tree `79d2098`, run id scfull2)

| gate | result |
|---|---|
| authoritative current-product suite | **46 expected / 0 unexpected / 0 flaky / 0 skipped** (121.1s) |
| vs pass-16's 45 | +1 is the new stale-cursor browser case; nothing was removed and all four pass-15 ports stay green |
| backend suite, same environment | 861 passed / 15 skipped / 0 failed (68.1s; was 836, +25 convergence cases) |
| Qoder/Sol truth contracts | 171 passed / 0 failed |
| SQLite contention | 0 |
| typecheck / typecheck:all / vite build | clean |
| legacy suite (non-gating, AI disabled) | 4 passed |
| mutation check | 8 sabotages, 7 killed, 1 survived with the reason above |

## Not reproduced, and why

Sol's stateful fuzz (60 x 30) and catastrophic mutation campaign (17/17) were not
re-run: this repository contains no property-based or stateful test at all
(`hypothesis`, `RuleBasedStateMachine` - zero hits), and Sol's
`real_api_state_machine.py`, `mutation_runner.py`, `concurrency_harness.py` and
`projection_oracle.py` live outside it in the verification snapshot.  Following
the handoff's own instruction not to force current-line counts to match a
disposable snapshot, what ships instead is deterministic concurrency schedules, a
differential projection oracle, and the eight-sabotage mutation log.  Whether the
fuzz and mutation harnesses should become permanent infrastructure here is asked
in report section 69.

## Mapping requested by section K

| defect | self-assessment | evidence |
|---|---|---|
| CX-SOL-001 execution cursor | CLOSED | report section 62; `test_sol_execution_cursor.py`; `qoder-stale-cursor.spec.ts`; mutation A killed |
| CX-EXT-002 same-proposal acceptance race | CLOSED | report section 64; two schedules in `test_sol_concurrency_and_remap.py`; mutation B killed |
| CX-EXT-003 competing proposals | CLOSED | report section 64; competing schedule asserts one ACTIVE plan and one ACCEPTED winner; mutation B killed |
| CX-EXT-004 capture versus accept | CLOSED | report sections 65 and 67; two schedules plus two direct re-anchor cases; mutations B and E killed |
| PROCESS_LOCAL_ONLY disclosure | `PROCESS_LOCAL_ONLY = True` in code, module docstring and call sites; not distributed safe | `app/concurrency_guards.py` |

Please verify rather than accept these self-assessments.

## Open question across lines

The GPT arbitration of pass-16 (report section 60) is still unanswered, and the
Sol handoff forbids resuming predictive-owner or place_id work until external
arbitration.  The ordering of those two rulings is asked in section 69.

## Contents

`provenance/authoritative.json` is what the gate recorded for the run behind
those numbers.  `runs/STATS.md` quotes the stats block, the SQLite-contention
count and the mutation tally out of the shipped files.  `tools/` carries the
scripts that produced the mutation and sensitivity logs.  `MANIFEST.txt` lists
every file with its SHA-256, generated by reading the finished archive back and
re-verified entry by entry.
