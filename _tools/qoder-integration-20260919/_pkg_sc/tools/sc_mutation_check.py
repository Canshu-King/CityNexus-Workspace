"""Mutation check for the Sol convergence suite.

A test that passes with the fix and also passes with the fix removed is not
evidence.  This script applies four targeted sabotages, one at a time, runs the
convergence suite against each, and prints which cases died.  Every file is
restored afterwards; nothing here is a permanent change.
"""

import io
import subprocess
import sys

SUITES = [
    "tests/test_sol_execution_cursor.py",
    "tests/test_sol_concurrency_and_remap.py",
]

MUTATIONS = [
    (
        "B: journey lock becomes a no-op",
        "app/concurrency_guards.py",
        """    key = str(journey_id)
    with _registry_guard:
        lock = _journey_locks.get(key)
        if lock is None:
            lock = RLock()
            _journey_locks[key] = lock
    with lock:
        yield""",
        "    yield  # SABOTAGE",
    ),
    (
        "E: capture stops re-anchoring its commitment",
        "app/commerce/service_impl.py",
        "        _remap_commitment_to_active_plan(session, commitment)",
        "        pass  # SABOTAGE",
    ),
    (
        "A: a stale cursor falls back like an absent one",
        "app/operations/v9.py",
        """    elif stale_cursor:
        current_index = len(activities)""",
        """    elif stale_cursor:
        current_index = next(
            (index for index, item in enumerate(activities) if item.status not in terminal),
            len(activities),
        )""",
    ),
    (
        "F: an unresolvable C4 is skipped instead of failing closed",
        "app/main.py",
        """            if protected:""",
        """            if False:""",
    ),
    (
        "F1: the resolver picks the first of many instead of AMBIGUOUS",
        "app/replanning/commitment_remap.py",
        """    if len(matches) > 1:
        raise RemapConflict(
            f"{subject} remap is AMBIGUOUS on the active Journey plan "
            f"({len(matches)} candidates carry the same identity)",
            matched=len(matches),
        )""",
        """    if len(matches) > 1:
        return matches[0]""",
    ),
    (
        "F2: the resolver returns nothing instead of failing on zero matches",
        "app/replanning/commitment_remap.py",
        """    raise RemapConflict(
        f"{subject} cannot be attached to the active Journey plan",
        matched=0,
    )""",
        """    return None  # SABOTAGE""",
    ),
    (
        "F3: identity falls back to suffix similarity",
        "app/replanning/commitment_remap.py",
        """        if identity.strong & candidate_strong:""",
        """        if identity.strong & candidate_strong or any(
            candidate.endswith(term) for candidate in candidate_strong | candidate_generic
            for term in identity.strong | identity.generic if term
        ):""",
    ),
    (
        "F4: the scheduled instant is not part of the anchor",
        "app/replanning/commitment_remap.py",
        """        if not _same_instant(identity.scheduled_at, moment):
            continue""",
        """        if False:
            continue""",
    ),
]


def run() -> tuple[int, list[str]]:
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "--no-header", *SUITES],
        cwd="backend",
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    failed = [
        line.split("::")[-1].split(" ")[0]
        for line in result.stdout.splitlines()
        if line.startswith("FAILED")
    ]
    summary = [line for line in result.stdout.splitlines() if " passed" in line or " failed" in line]
    return result.returncode, [summary[-1] if summary else "?", *failed]


print("=== baseline (no sabotage) ===")
print(run())

for label, path, old, new in MUTATIONS:
    full = "backend/" + path
    original = io.open(full, encoding="utf-8", newline="").read()
    if old not in original:
        print(f"!! {label}: anchor not found, skipping")
        continue
    try:
        io.open(full, "w", encoding="utf-8", newline="").write(original.replace(old, new, 1))
        code, detail = run()
        verdict = "KILLED" if code else "SURVIVED"
        print(f"=== {label}: {verdict} -> {detail}")
    finally:
        io.open(full, "w", encoding="utf-8", newline="").write(original)

print("=== all files restored ===")
print(subprocess.run(["git", "status", "--porcelain"], cwd=".", capture_output=True, text=True).stdout)
