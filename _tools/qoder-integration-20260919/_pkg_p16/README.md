# Qoder pass-16 — activity identity, a commitment that exists, and prevention with an owner

Answers the pass-15 ruling's four judgement calls (report sections 52-60).  No
capability was retired, no assertion was widened, and the one claim this pass
could not prove is reported as withdrawn rather than quietly dropped.

## What changed

| commit | what |
|---|---|
| `05a06bf` | backend: `place_id` survives the `/experience` projection, plus two chain regressions |
| `564bf3b` | e2e: a shared `protectCommitment()` fixture; all commitment claims by identity |
| `6311382` | frontend: `V14PreventivePanel` on `/v8/authoritative`; the v6 case asserts it structurally |
| `86f7270` | docs: the two documents that still described pass-14 |
| `967e2b2` | e2e: settle the discovery card before capturing it (see the evidence note below) |
| `967e2b2` | e2e: the run's own prediction provenance, asserted (see the real-city note) |

## C. the identity defect, diagnosed to a layer before being fixed

The pass-15 report noted `/experience` returning `place_id: null` on the accepted
plan while `/plans/generate` populated it.  Measured on one run: the canonical
child plan reported `place_id` on 6/6 activities, the same plan through
`/experience` on 0/6 - so identity was lost in the projection, not in the solver
or in acceptance.  Fixed there.  The regression does not assert "the field
exists"; it walks generate -> select -> start -> closure -> request_replan ->
accept and compares the two projections by place id, then asserts that a
replacement activity also carries a real place id so a null cannot sneak past the
comparison.

## A/B. the fixture had nothing to protect

Measured: the demo cruise is `locked: true` and `protected: false` until a booking
exists and its payment is captured, because `protected` is derived from ACTIVE
Commitment rows.  So golden, the envelope case and the zero-touch case were each
asserting "the protected commitment survived" over a fixture with no protected
commitment, and the flag they read was true for the wrong reason.

All four cases now create the real thing through the traveller's own path -
`POST /bookings`, then a CAPTURE transaction with an `Idempotency-Key`, before
`/start` because booking a travelling activity answers 422 - via one shared
helper that re-reads `/experience` and throws if the commitment did not land.

## D/E. prevention now has a surface owner, and the red is gone by fixing it

`V14PreventivePanel` reads the `GuardianRun` itself rather than a plan diff, so it
cannot be a reactive recovery wearing a different label: TRIGGER is the run's
`trigger_kind`, the timing chip is
`evidence.observation.forecast_before_hard_failure`, FORECAST is the snapshot the
run acted on, and the plan line carries both plan ids as data attributes.  The
reactive panel stays beneath it and the copy says which one owns what.

The v6 case dropped its body-text sentinel - the one pass-15 admitted could be
falsely greened by any unrelated use of the word "forecast" - for assertions bound
to the guardian run id.  It also now files a real forecast payload
(`risk_score: 88`) and requires `forecast_risk == 88` in the snapshot, the
`ORTOOLS_CP_SAT_V2` solver kind, a replay-provenanced OpenStreetMap candidate in
the provider mesh, and zero `/guardian/scan` requests.

Three facts only appeared by running it:

- the aggregate resilience score **saturates**: a filed forecast of 88 renders as
  `risk 100` once the other components stack, so the panel and the test both read
  the `forecast_risk` component;
- a `GuardianRun` row is written as `RUNNING / PLANNING` before the recomposition
  lands, so polling for its appearance asserted on a half-finished action; the
  case now waits for that same run id to reach `COMPLETED`;
- the panel stops polling once the run exists - a run is durable evidence, and a
  3-second poll beside the autopilot's own writes buys only SQLite contention.

## One claim withdrawn, not softened

The case initially required the prevented plan to contain a `real-place-*`
activity.  It does not: the recomposition moved `place-tech-art` to
`place-city-park` and bought schedule slack.  The pytest v6 case only gets a
real-place activity because it seeds specific legs as explicit replay facts, which
changes what the solver considers affordable.  Asserting it here would have tested
the fixture, so it is gone, and what is provable is asserted instead (provider
mesh + the recomposition fingerprint printed in the run log).  `v13-5-fully-grounded`
remains the owner of "a real place entered the plan".

## The real-city half, proven from the run rather than from its name

The ruling refused `trigger_kind=PREDICTIVE` as evidence of a grounded real-city
prediction, so the case reads the run's own `evidence.prediction.evidence_provenance`
and requires it to be non-empty, `REPLAY` for **every** entry (not a mock default
laundered into a hard fact), and to name at least one replay provider.  Measured on
this journey: `open-meteo-replay` (CITY_SIGNAL) and `city-signal-fixture` (MOBILITY),
both REPLAY, with three real-city candidates in the provider mesh - all printed into
the run log so the claim and the data travel together.

One thing this pass did not eliminate: repeated single-spec runs of the prevention
case produced two occurrences of `JourneyTwin cache write skipped ... database is
locked`, a contention path the backend catches explicitly and which changed no
assertion.  All three full authoritative runs recorded zero.  Reported as observed,
not as fixed.

## Evidence hygiene: a case that passed while shipping a blank screenshot

The first full authoritative run on tree 6311382 was 45/0, but the regenerated
`reports/product-v13.5/fully-grounded-discovery.png` shrank from 133910 to 91550
bytes and showed an empty page - while every assertion in that spec had passed.
The result card fades in and `toBeVisible()` is already true at opacity 0; the
previous pass had caught it mid-fade, this one caught it before the fade.

Fixed in `967e2b2` by waiting for that subtree's animations to reach a terminal
state (document-wide is impossible: the app runs infinite pulse dots).  The
quoted run below is the rerun on that tree.  The other eight regenerated images
were pixel-diffed rather than eyeballed: the largest is
`mobility-sheet-desktop` at 37.6% changed pixels, which is the fullPage anchor of
the modal plus the clock and map nodes - same surface, same five modes, same
banner - and none of them went blank.

## Numbers (one authoritative run, tree `967e2b2`, run id p16full3)

| gate | result |
|---|---|
| authoritative current-product suite | **45 expected / 0 unexpected / 0 flaky / 0 skipped** (115.6s) |
| vs pass-15's 44/1 | the 1 was D; it is green because V8 grew an owner, not because an assertion was removed - the total stays 45 |
| `qoder-*` | 31 results / 0 failed |
| SQLite contention warnings | 0 |
| typecheck / typecheck:all / vite build | clean (build 4.70s) |
| backend suite, same environment | 836 passed / 15 skipped / 0 failed (56.7s; +2 = the identity contract) |
| legacy suite (non-gating) | 4 passed with the AI switch disabled; 3 passed / 1 failed inheriting a host `DEEPSEEK_API_KEY` |

The legacy delta is a real product observation, recorded in
`docs/LEGACY_E2E_MIGRATION.md`: with a live key the flagship Guardian scan goes
through the model and may return `MODEL_NO_MUTATION` where the archived case wants
`EXECUTED`.  Its numbers must always travel with the AI switch state.

## Asked of the arbiter

INTEGRATION_REPORT.md section 60: whether the withdrawn real-place claim is
accepted, whether `V14PreventivePanel` closes D or must also appear on `/v8/live`,
whether `locked_commitments_preserved` should be demoted to an informational field
now that plans are compared by identity, whether
`INTEGRATION_CANDIDATE_READY_FOR_MAIN` can be signed or whether the RC items still
block it, and whether the settle-before-capture wait should become a general
precondition of the screenshot gates.

## Contents

`provenance/authoritative.json` is what the gate recorded for the run behind those
numbers.  `runs/STATS.md` quotes the stats block out of the shipped JSON, including
the SQLite-contention count taken from the shipped stderr log.  `MANIFEST.txt`
lists every file with its SHA-256, generated by reading the finished archive back
and re-verified entry by entry.
