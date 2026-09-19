"""Adapt the pass-14 packaging script for pass-15."""

import io

PATH = "_build_pkg_p15.py"
src = io.open("_build_pkg_p14.py", encoding="utf-8").read()

pairs = [
    ('STAGE = os.path.join(ROOT, "_pkg_p14")', 'STAGE = os.path.join(ROOT, "_pkg_p15")'),
    ('NAME = "CityNexus-Qoder-pass14-Canonical-E2E-Policy-Legacy-Archive-20260919.zip"',
     'NAME = "CityNexus-Qoder-pass15-PortFirst-Convergence-20260919.zip"'),
    ('GATES_SUBJECT = "test(e2e): pass-14"', 'GATES_SUBJECT = "test(e2e): pass-15 D"'),
    ("# pass-14 archive manifest", "# pass-15 archive manifest"),
    ('"Every number in INTEGRATION_REPORT.md sections 40-44 was produced on tree %s.\\n"',
     '"Every number in INTEGRATION_REPORT.md sections 46-50 was produced on tree %s.\\n"'),
    ("CITYNEXUS_E2E_RUN_ID=p14full1", "CITYNEXUS_E2E_RUN_ID=p15full1"),
    ("CITYNEXUS_BACKEND_PORT=8036 CITYNEXUS_E2E_PORT=4208", "CITYNEXUS_BACKEND_PORT=8047 CITYNEXUS_E2E_PORT=4219"),
    ("sqlite:///./_p14full1.db", "sqlite:///./_p15full1.db"),
    ('"01_pass14_policy_and_legacy_archive.patch"', '"01_pass15_port_first_delta.patch"'),
    # the pass-15 delta spans three commits, so patch from the previous package's HEAD
    ('    handle.write(git_b("show", "--format=%n%n%s%n%n%b", gates))',
     '    handle.write(git_b("diff", PASS14_HEAD, gates))'),
    ('GATES_SUBJECT = "test(e2e): pass-15 D"',
     'GATES_SUBJECT = "test(e2e): pass-15 D"\nPASS14_HEAD = "5cac395d"'),
    ("""    ("p14_full.json", "runs/fe_full_pass14_authoritative.json"),
    ("p131_full.json", "runs/fe_full_pass131_authoritative.json"),
    ("p14_backend.log", "runs/backend_p14.log"),
    ("p14_legacy.log", "runs/legacy_suite_p14.log"),""",
     """    ("p15_full.json", "runs/fe_full_pass15_authoritative.json"),
    ("p14_full.json", "runs/fe_full_pass14_authoritative.json"),
    ("p15_backend.log", "runs/backend_p15.log"),
    ("p14_legacy.log", "runs/legacy_suite_p14.log"),"""),
    ("""    for label, fname in (
        ("pass-14 authoritative current-product suite, tree %s" % gates[:7], "fe_full_pass14_authoritative.json"),
        ("pass-13.1 authoritative suite (before the four archives)", "fe_full_pass131_authoritative.json"),
    ):""",
     """    for label, fname in (
        ("pass-15 authoritative current-product suite, tree %s" % gates[:7], "fe_full_pass15_authoritative.json"),
        ("pass-14 authoritative suite (before the ports)", "fe_full_pass14_authoritative.json"),
    ):"""),
    ('("docs/E2E_ACCEPTANCE_POLICY.md", "E2E_ACCEPTANCE_POLICY.md"),',
     '("docs/E2E_ACCEPTANCE_POLICY.md", "E2E_ACCEPTANCE_POLICY.md"),'),
]
for old, new in pairs:
    if old not in src:
        raise SystemExit("expected to find: %r" % old[:70])
    src = src.replace(old, new, 1)

# the docs-only guard must allow the pass-15 spec files, which are the deliverable
src = src.replace(
    """between = git("diff", "--name-only", gates, head).splitlines()
outside = [p for p in between if p != "INTEGRATION_REPORT.md" and not p.startswith("reports/")]
if outside:
    raise SystemExit("HEAD is no longer report-and-evidence only over the gates tree: %s" % outside)""",
    """between = git("diff", "--name-only", gates, head).splitlines()
outside = [p for p in between if p != "INTEGRATION_REPORT.md" and not p.startswith("reports/")]
if outside:
    raise SystemExit("HEAD is no longer report-and-evidence only over the gates tree: %s" % outside)""",
)

start = src.index('readme = """')
marker = '""".format(gates=gates[:7], head=head[:7])'
end = src.index(marker) + len(marker)

README = '''readme = """# Qoder pass-15 — three port-first capabilities now live on the current product, and one red test that names a product gap

Executes the pass-14 ruling in the order it set: golden -> envelope-safe
recovery -> zero-touch autopilot -> predictive prevention.  Nothing was
redirected to `/legacy`, nothing skipped, nothing softened into an
API-only assertion.

## What changed

| commit | what |
|---|---|
| `3e9059f` | A golden ported to V8 Live, plus the two pass-14 hygiene comments |
| `d664143` | B envelope-safe autonomous recovery and C zero-touch autopilot, both on current surfaces |
| `{gates}` | D predictive prevention left red with the gap named, plus the report |

`COMMITS.txt` prints the file list for the tree the gates ran on.

## A. golden — persistence proven by identity, not by text

closure event -> proposal presented on the current Live surface -> the traveller
accepts through the product's own control -> the accepted plan identity is server
truth (journey and twin agree) -> reload renders the resolved state instead of
asking again -> the protected commitment is still on the plan.

Two measurements recorded rather than hidden:

- `/journeys/{id}/plans/generate` populates `activity.place_id`, but `/experience`
  reports `place_id: null` for all six activities of the accepted plan.  The
  commitment is therefore matched on the title the traveller sees, and the test
  prints the discrepancy.  The current payload cannot prove "the same place is
  still protected".
- the legacy exact localStorage key whitelist would fail for a legitimate reason
  (the Copilot dock stores per-journey chat history), so the assertion checks what
  matters: no plan-shaped key, and no stored value containing the accepted plan id.

Setup walks the product's own transitions because `request_replan` answers
409 `journey must be ACTIVE with an active plan` otherwise.

## B. envelope-safe recovery

The gateway decides `ALLOW_AUTO` under the traveller's own policy, executes, the
executed child plan version becomes authoritative, cost and drift deltas stay
inside the configured envelope, locked commitments survive, and
`/v8/authoritative` renders the accepted version id with the C4-preserved line and
provider evidence.  Policy limits are read back after the PUT: "inside the
envelope" is meaningless if the envelope was never stored.  Measured:
`cost delta -3000 of 5000, drift -5 of 120`.

## C. zero-touch, kept distinct from B

After one provider-shaped event the test performs no click, no fill and no accept.
The plan identity changes on its own, the linked proposal is `ACCEPTED` with
commitments preserved, the audit feed attributes it to
`replan_auto_accepted / AI_AGENT`, Live no longer asks about a recovery that
already happened, and reload keeps the plan id.

The first version guessed the feed path and wrapped it in `.catch()`, which turned
a 404 into an empty list and the proof into nothing.  The endpoint is
`/journeys/{id}/agent-feed`; the swallow is gone.

## D. prevention exists, and V8 has no owner for it — left red

With only a `RISK_FORECAST` signal, and with the test asserting that the journey
carried no CLOSURE or CRITICAL event at that moment, the autopilot produces
`decision=PREEMPTIVE_RECOVERY`, `trigger_kind=PREDICTIVE`,
`action_status=EXECUTED`, `forecast_before_hard_failure=true`, changes the
authoritative plan, keeps the protected commitment, and issues zero `/guardian/scan`
requests.

Every component that renders a preventive run — `guardian-decision`,
`guardian-predictive-resilience`, `guardian-provenance`, `guardian-trace`,
`guardian-standing-mission`, `guardian-provider-risk-forecast` — exists only in
`src/main.tsx`, behind `/legacy`.  `api/citynexus.ts` still types
`PREEMPTIVE_RECOVERY` and `trigger_kind`; no V8 component references them.  The
capability is real and invisible to the traveller.

The test therefore fails on purpose, with a message that names the gap and the two
forbidden shortcuts (no backend-only green, no relabelling reactive as
prevention).  Its assertion is text-level and says so: false today, which is what
makes the gap provable, to be replaced by a structured assertion when V8 grows an
owner.

## Numbers (one authoritative run, tree `{gates}`)

| gate | result |
|---|---|
| authoritative current-product suite | **44 expected / 1 unexpected / 0 flaky** (122.2s) |
| the 1 | `predictive-real-city-v6`, the product gap above |
| vs the predicted 45/0 | one-for-one holds: the total is still 45 and three of the four ports are green; the remaining red is the gap, not unfinished migration |
| legacy discovered by the acceptance suite | none |
| `qoder-*` | 31 passed / 0 failed |
| typecheck / typecheck:all / vite build | clean |
| backend, same environment | 834 passed / 15 skipped / 0 failed |
| SQLite contention warnings | 0 |

## Asked of the arbiter

INTEGRATION_REPORT.md section 51: whether the D gap is approved as a red test plus
a scheduled product line (and the minimal V8 owner I would propose), whether the
text-level assertion is acceptable as a transition, whether the
`place_id`-null contract inconsistency should be fixed or recorded, and whether
`INTEGRATION_CANDIDATE_READY_FOR_MAIN` can now be defined as
"authoritative current-product 0 unexpected + D has an owner".

## Contents

`provenance/authoritative.json` is what the gate recorded for the run behind those
numbers.  `MANIFEST.txt` lists every file with its SHA-256, generated by reading the
finished archive back and re-verified entry by entry.
""".format(gates=gates[:7], head=head[:7])'''

src = src[:start] + README + src[end:]
io.open(PATH, "w", encoding="utf-8", newline="\n").write(src)
print("wrote", PATH, len(src))
