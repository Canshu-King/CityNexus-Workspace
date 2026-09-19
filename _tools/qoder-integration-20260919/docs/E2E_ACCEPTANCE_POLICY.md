# E2E acceptance policy — what is allowed to sign a gate

Status: **binding** since the pass-13.1 ruling (2026-09-19).
Owner: the acceptance criteria are the arbiter's; this file records them so a
lane cannot quietly decide for itself which run counted.

## The rule

**Only an Authoritative E2E run may be used as evidence for integration
arbitration, merge readiness, or release candidates.**

Any other Playwright run — a bare `npx playwright test`, anything with
`reuseExistingServer: true`, anything that did not print a provenance line — is a
local developer diagnostic.  It may be pasted into a debugging conversation.  It
cannot sign a gate, and a claim of "E2E is green on my machine" without
authoritative provenance is equivalent to "there is a computer nearby that seems
happy".

This applies to every lane that claims an E2E result (Qoder today; Codex/dsh/Astra
if and when they do).  Lanes that only read another lane's tree, package, or
results are unaffected — reading evidence is not producing it.

## Why this exists

Pass-12 found that the frontend suite in a clone was testing whatever happened to
own port 8000.  The clone had no `.venv`, so `playwright.config.ts` fell back to a
system Python that cannot import the app, and `reuseExistingServer: true` silently
adopted another agent lane's backend: different code, different database, DeepSeek
switched on.  The same HEAD produced 34/12, then 35/11, then 37/9 across passes, and
each number was real for a different server.

## What an authoritative run must satisfy

| # | requirement | where it is enforced |
|---|---|---|
| 1 | `CITYNEXUS_E2E_AUTHORITATIVE=1` | `frontend/playwrightEnv.ts` |
| 2 | `CITYNEXUS_PYTHON`, frontend port, backend port, run id and database URL all explicit; no fallback to system Python; ports distinct | `playwrightEnv.ts` |
| 3 | `reuseExistingServer: false` for **both** webServers | `playwright.config.ts` |
| 4 | the database is **fresh-or-no-run**: a throwaway `_<runId>.db`, and a run-stamped process refuses to reopen a file that already exists (never auto-deleted) | `backend/app/db/session.py`, pinned by `backend/tests/test_e2e_provenance.py` |
| 5 | external AI disabled: no `DEEPSEEK_API_KEY` / `CITYNEXUS_AI_API_KEY` present and `CITYNEXUS_AI_ENABLED=false` | `playwrightEnv.ts` |
| 6 | the provenance response belongs to *this* invocation: `globalSetup` reads `/health` **through the frontend origin** and requires the per-run token, the database basename and `ai=disabled` to match what it asked for | `frontend/e2e/_qoderAuthoritativeSetup.ts`, `backend/app/main.py` |
| 7 | non-authoritative results may diagnose but cannot sign | this document |
| 8 | no Git/SHA hash gate | deliberately absent |

Point 6 goes through the frontend on purpose: the tests exercise
`vite dev server → proxy → uvicorn`, so an answer that arrives with the right token
over the frontend origin proves both processes belong to the run, not just the one
on the API port.

`/health` echoes `e2e_run_id` and `e2e_database_id` (a basename) and never a
connection URI — a field added for test provenance must not become the place a
future `postgresql://user:password@host` leaks.  That boundary is a test, not a
convention.

The provenance record is printed to **stderr** (stdout stays parseable for
`--reporter=json`) and written to `reports/e2e-provenance/authoritative.json`, which
belongs in every delivered evidence package.

## The command

```
CITYNEXUS_E2E_AUTHORITATIVE=1 CITYNEXUS_E2E_RUN_ID=<unique-id> \
DEEPSEEK_API_KEY= CITYNEXUS_AI_API_KEY= CITYNEXUS_AI_ENABLED=false \
CITYNEXUS_PYTHON='<absolute path to a python that can import the app>' \
CITYNEXUS_BACKEND_PORT=<free port> CITYNEXUS_E2E_PORT=<another free port> \
CITYNEXUS_DATABASE_URL='sqlite:///./_<same-unique-id>.db' \
  npx playwright test --reporter=json
```

Run it from `frontend/`.  The database path is resolved relative to `backend/`.

## Suite layout

| what | where | gating? |
|---|---|---|
| current-product acceptance suite | `frontend/e2e/**` except `e2e/legacy/` | **yes** — this is the suite whose numbers sign gates |
| archived legacy-surface tests | `frontend/e2e/legacy/` | **no** — run with `npx playwright test --config playwright.legacy.config.ts` |
| legacy Journey Mode app | served only under `/legacy` by `src/main.tsx` | n/a |

The authoritative config sets `testIgnore: /[\\/]e2e[\\/]legacy[\\/]/`, so archived
cases are not discovered by an acceptance run.  The legacy config cannot be made
authoritative: passing the flag there is reported and ignored.  Archiving means the
default suite stops counting a test — moving it to another project that the default
run still executes would be a reorganisation, not a retirement.

## Known-red by design (currently none)

Pass-14 shipped with four deliberate reds: `golden.spec.ts`,
`live-autopilot-v5.spec.ts`, `product-hardening.spec.ts` (autonomous envelope-safe
recovery) and `predictive-real-city-v6.spec.ts`.  They were ported, not skipped and not
deleted — pass-15 re-expressed three of them on the current V8 surface and pass-16 gave
prevention a current owner — so the acceptance suite is now 45 expected / 0 unexpected.

The principle stands and is the reason this section exists rather than being deleted
with the reds: a red test that names unfinished work is worth more than a green test that
hides it.  If a future pass leaves a case red, its failure message has to name the
product gap it is standing for and the shortcut that would falsely green it (relabelling,
narrowing the assertion, or moving the proof to a layer the user never sees).

## Explicitly not required

A Git-SHA / build-hash verification gate.  Process ownership (points 2, 3 and 6) is
what makes "did we test our own tree" true, and it is mechanical; re-verifying
artefact hashes on top of that was considered and rejected as ceremony.
