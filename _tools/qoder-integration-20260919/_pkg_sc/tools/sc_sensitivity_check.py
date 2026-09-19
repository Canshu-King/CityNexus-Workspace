"""Sensitivity check: does the race suite actually detect a missing guard?

A test that passes with the fix and also passes without it proves nothing.  This
script temporarily replaces the Journey lock with a no-op, runs the three race
cases, and restores the file.  It prints what happened rather than asserting a
convenient outcome.
"""

import io
import subprocess
import sys

PATH = "backend/app/concurrency_guards.py"
original = io.open(PATH, encoding="utf-8", newline="").read()

sabotaged = original.replace(
    """    key = str(journey_id)
    with _registry_guard:
        lock = _journey_locks.get(key)
        if lock is None:
            lock = RLock()
            _journey_locks[key] = lock
    with lock:
        yield""",
    """    yield  # SABOTAGE: guard removed""",
    1,
)
assert sabotaged != original, "sabotage anchor did not match"

TARGETS = [
    "tests/test_sol_concurrency_and_remap.py::test_concurrent_acceptance_of_the_same_proposal_produces_one_transition",
    "tests/test_sol_concurrency_and_remap.py::test_replaying_the_same_idempotency_key_never_transitions_twice",
    "tests/test_sol_concurrency_and_remap.py::test_competing_proposals_can_never_both_become_active",
    "tests/test_sol_concurrency_and_remap.py::test_capture_and_accept_racing_leave_no_stranded_commitment",
    "tests/test_sol_concurrency_and_remap.py::test_the_guard_actually_serialises_two_threads_for_one_journey",
]

try:
    io.open(PATH, "w", encoding="utf-8", newline="").write(sabotaged)
    print("=== guard removed; the suite should go red ===")
    for target in TARGETS:
        result = subprocess.run(
            [sys.executable, "-m", "pytest", "-q", "--no-header", target],
            cwd="backend",
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        tail = [line for line in result.stdout.splitlines() if " passed" in line or " failed" in line or "assert" in line]
        print(target.split("::")[-1], "->", "RED" if result.returncode else "GREEN", "|", (tail[-1] if tail else "")[:110])
finally:
    io.open(PATH, "w", encoding="utf-8", newline="").write(original)
    print("=== guard restored ===")
