# Codex review — interference check + code-quality assessment

Date: 2026-09-12 02:55 (+08:00)
Scope: concurrent edits made to `D:\moodle\CityNexus` by a second agent (Codex) between
02:08 and 02:51, while the Guardian evidence fix was being written.
Repo state: `backend/` and `frontend/` are **not git-tracked** (last commit is
`7d22cd0 feat(visio): ...`), so every conclusion below is from the working tree only.

---

## Part 1 — Interference check: did Codex's edits break the fix?

**No. The fix is intact and the gates still pass.**

`backend/app/agent/guardian.py` was rewritten by Codex at **02:45:59**, one second after
the fix landed. Re-verified by reading the file back, not by trusting timestamps:

```
$ grep -n "accept_arguments\|request_result\|proposal_payload" backend/app/agent/guardian.py
236:    request_result = request_step.get("result") if request_step else {}
237:    proposal_payload = request_result.get("proposal") if isinstance(request_result, dict) else None
238:    if isinstance(proposal_payload, dict) and proposal_payload.get("id"):
239:        run.proposal_id = str(proposal_payload["id"])
240:    accept_arguments = accept_step.get("arguments") if accept_step else None
241:    if isinstance(accept_arguments, dict) and accept_arguments.get("proposal_id"):
246:        run.proposal_id = str(accept_arguments["proposal_id"])
```

`backend/tests/test_guardian_model_evidence.py` (236 lines) is also untouched.

Codex's edits to `guardian.py` were **additive**: it defined the missing `_load` helper
that the file had been calling at lines 650/778 without ever defining. That was a
pre-existing `NameError` waiting to fire on the predictive path; Codex closed it.

### Test results against the latest code (post-02:51)

| Run | Result |
|---|---|
| `test_guardian_model_evidence.py test_v6_predictive_real_city.py test_v5_autopilot.py test_guardian_v4.py test_agent_runtime_gate.py` | **29 passed** |
| Full suite, `pytest -q` with isolated DB | **322 passed, 2 skipped**, 95.35s |

Zero failures. The 2 skips are pre-existing markers. Services on 8000 and 5173 both
return HTTP 200 and serve live DB data; the demo environment is healthy.

### Concurrency note

Codex was still writing when the assessment ran — `services.py` 02:50:06, `autorun.py`
02:51:16, `main.tsx` grew from 1408 to 1488 lines after 02:37. The full-suite run
overlapped the 02:51 `autorun.py` write, so the 322-pass figure is against a slightly
moving target. The targeted 29-test run was done after the last observed write.

---

## Part 2 — Codex's change set

| Time | File | Kind |
|---|---|---|
| 02:08 | `backend/app/core/config.py`, `db/models.py`, `db/session.py`, `schemas.py` | batch |
| 02:21 | `backend/app/integrations/discovery/real_city.py` | new real-city POI discovery |
| 02:27 | `frontend/src/api/citynexus.ts`, `components/JourneyMap.tsx` | API + map |
| 02:29 | `backend/app/main.py` | routes |
| 02:30 | `backend/tests/test_v6_predictive_real_city.py` | **new test (136 lines)** |
| 02:36 | `frontend/e2e/predictive-real-city-v6.spec.ts` | **new e2e (87 lines)** |
| 02:37 | `frontend/src/main.tsx` | predictive UI panel |
| 02:40 | `backend/app/agent/predictive.py`, `signal_pipeline.py` | resilience + signal pipeline |
| 02:45 | `backend/app/agent/guardian.py` | added missing `_load` |
| 02:50 | `backend/app/services.py` | service layer |
| 02:51 | `backend/app/agent/autorun.py` | pulse worker |

Theme: one coherent V6 feature — **predictive** (pre-emptive) recovery, where the Guardian
acts on a *forecast* before the journey becomes infeasible, instead of reacting to a
break. That is a genuine step up in ambition from the V5 reactive autopilot.

---

## Part 3 — Code quality

### What is good

**1. Test-first, and the tests are real.**
`test_v6_predictive_real_city.py` is API-driven end-to-end, not a unit stub. It asserts
`provenance == REPLAY`, real Tianjin/Haihe candidates, `trigger_kind == "PREDICTIVE"`,
`decision == "PREEMPTIVE_RECOVERY"`, `solver.kind == ORTOOLS_CP_SAT_V2`, 6 counterfactuals,
and — the assertion that matters most — `domain_truth_mutated is False`. That last one is
the test of whether the "what-if" simulation leaks into the real plan. Asserting it
explicitly is the mark of someone who has been burned by exactly that bug.

**2. The e2e spec asserts autonomy, not just output.**
`predictive-real-city-v6.spec.ts` counts `/guardian/scan` requests and asserts
`expect(guardianScanRequests).toBe(0)`. A weaker test would only check the UI shows
`EXECUTED`; this one proves the recovery happened *without* a manual scan. It also
reloads the page and re-asserts persistence, and uses `page.waitForResponse(...)` for
every mutation instead of `waitForTimeout` — no flaky sleeps.

**3. Exception handling is deliberate and annotated.**
`autorun.py:191` catches broad `Exception` but documents why:
`# provider/agent boundary: preserve worker liveness`. `autorun_status()` degrades to
`enrolled = []` rather than failing the status endpoint. Both are correct choices for a
background worker. There are **0** bare `except:` clauses across the five main modules.

**4. Strong, consistent internal conventions.**
`from __future__ import annotations` everywhere; 14/16 functions in `predictive.py` carry
return annotations; module-private `_now()` / `_json()` / `_load()` helpers duplicated
consistently rather than cross-imported; `frozenset` for membership sets
(`ACTIONABLE_EVENT_TYPES`, `FIXTURE_STATES`); `ensure_ascii=False, sort_keys=True` on every
`json.dumps` so fingerprints are stable.

**5. The snapshot design is genuinely good.**
`build_resilience_snapshot` computes a SHA-256 `fingerprint` over the material payload and
returns the existing row on a match (line 336-343). That makes snapshot creation idempotent
without a lock. `_load(..., default)` never lets a malformed JSON column take down a read.
The `evidence` dict is separated into `observation` / `inference` / `solver` / `policy` /
`mutation` lanes — an audit model most production systems do not bother with.

### What is weak

**1. No type checking on the frontend at all.** ← the biggest concrete gap
There is **no `tsconfig.json` anywhere** under `frontend/`. `vite.config.ts` and
`playwright.config.ts` exist; the compiler config does not. Vite/esbuild strips types
without checking them, so `main.tsx` — now **1488 lines** — has never been type-checked.
`package.json` has no `typecheck` and no `lint` script. Confirmed by running
`tsc --noEmit`, which printed the help text because it had no project to build.

**2. Ruff is not clean: 9 findings.**
```
app\agent\autorun.py:209:5    SIM117  nested with
app\agent\autorun.py:298:12   BLE001  blind except Exception
app\agent\predictive.py:20:5  F401    JourneyTwin imported but unused
app\agent\predictive.py:95    DTZ007  naive datetime from strptime
app\agent\predictive.py:496:5 F841    local `plan` assigned, never used
app\main.py:1:1               I001    imports unsorted
app\main.py:91:5              F401    JourneyResilienceSnapshot imported but unused
tests\test_v6_predictive_real_city.py:1:1  I001 imports unsorted
tests\test_v6_predictive_real_city.py:3:8  F401 `json` imported but unused
```
Four of these (both F401s in `main.py`/`predictive.py`, the unused `plan`, the unused
`json` in the new test) are dead code left behind after an edit. None is dangerous; all
are the residue of fast iteration without running a lint gate. The project has `ruff`
installed but evidently does not run it in CI.

**3. Comment density near zero.**
`predictive.py` 603 lines / 4 comment lines; `signal_pipeline.py` 685 / 6;
`services.py` 666 / 10. The names are good enough that it mostly reads, but the *reasoning*
is not recorded. Where Codex does comment, it is exactly where it should be — the
`_model_recovery` proposal-id comment and the `_load`/`_future` intent comments are the
highest-value lines in the diff. The problem is that this is the exception, not the rule.

**4. `_future` is a dead filter** — full write-up in `_autopilot_finding_20260912.md`
(Finding 2). `_future(activity, journey)` compares `activity.end_at >= journey.start_at`,
which is true for every activity in a running journey. Empirically 6 of 6 activities
counted as "future", including one with `status == "COMPLETED"`. Bounded impact so far
(extra `risk_score: 0` rows; top-line score and `STABLE` status unchanged), but it is a
predicate that does not do what its name says. **Ownership unknown** — no older copy of
`predictive.py` exists anywhere in the workspace, so I cannot attribute it to Codex.

**5. No DB isolation for tests.**
The repo has no `conftest.py`. Tests fall back to `sqlite:///./citynexus.db` relative to
the CWD, which is the same file the running uvicorn uses. That is why an earlier full-suite
run produced one `StaleDataError` failure purely from the suite colliding with the live
server. Every full run currently needs a manual `CITYNEXUS_DATABASE_URL` override.

---

## Verdict

**Senior-level backend engineer, mid-level frontend discipline.**

The architecture is the work of someone who has shipped real distributed systems. The
`evidence` lane model, the fingerprint-idempotent snapshots, the one-use HMAC approval
receipts, the `Idempotency-Key` requirement on mutations, the constant-time
`hmac.compare_digest`, the optimistic-concurrency `rowcount != 1` guard, and the
`domain_truth_mutated is False` assertion are all patterns you learn by getting them wrong
in production. The V6 predictive feature is a real capability increase, not a rename, and
it landed with a backend test and an e2e test that check the *hard* properties.

The weaknesses are all of one kind: **no gates.** No `tsconfig.json`, no lint script in
`package.json`, ruff findings left unfixed, a `_future` predicate whose name lies, and no
test DB isolation. Nothing here is a design error; every one is something a CI pipeline
would catch in ten seconds. It reads like a very strong engineer moving fast in an
environment where nothing is checking their output — which is exactly what is happening,
since `backend/` and `frontend/` are untracked and there is no CI.

### Highest-value next steps (in order)

1. Add `frontend/tsconfig.json` + a `typecheck` script and run it. 1488 unchecked lines
   in `main.tsx` is the single largest latent risk in the tree.
2. Add `backend/tests/conftest.py` that pins `CITYNEXUS_DATABASE_URL` to a temp DB, so the
   suite stops fighting the dev server.
3. Clear the 9 ruff findings and add `ruff check` to whatever runs before a review package.
4. Decide `_future`'s intended semantics and make the code match — do this *with* Codex, or
   after it stops writing, to avoid a conflicting edit.

### Do not touch

- `guardian.py` lines 236-251 (the fix) — verified present, but re-grep before packaging.
- The `_server_8000.log` / running uvicorn on 8000 — deleting a log file that a live
  process holds open crashes it on Windows. Learned the hard way at 02:38.
