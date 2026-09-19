#!/usr/bin/env python3
"""Disposable-clone mutation gate for semantic catastrophe regressions.

Each mutant is an exact, reversible text substitution.  The runner records the
diff, focused gate, exit code and first killing test; the source is restored in
``finally`` after every case.
"""
from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1] / "snapshot" / "citynexus"
BACKEND = ROOT / "backend"
PYTHON = BACKEND / ".venv" / "Scripts" / "python.exe"
OUT = Path(__file__).resolve().parents[1] / "closeout_20260919" / "raw" / "final" / "mutation_results.json"


def pytest(path: str, extra: str = "") -> list[str]:
    return [str(PYTHON), "-m", "pytest", "-q", path, *extra.split()]


MUTANTS = [
    {"id": "J-ACK-RESOLVED", "path": "backend/app/planning/hard_recovery.py", "old": 'event.status = "ACKNOWLEDGED"', "new": 'event.status = "RESOLVED"', "cmd": pytest("tests/test_v1923_final_code_gate.py", "-k acknowledge_never")},
    {"id": "J-CROSS-JOURNEY-TRIGGER", "path": "backend/app/main.py", "old": 'if trigger_event is None or trigger_event.journey_id != journey.id:', "new": 'if trigger_event is None:', "cmd": pytest("D:/moodle/_codex_sol_extreme_v2_20260919/tests/test_mutation_survivor_regressions.py", "-k cross_journey")},
    {"id": "J-ACK-CLOSES-UNRELATED", "path": "frontend/src/lib/disruptionState.ts", "old": 'if (acceptedTriggerIds.has(String(item.id))) return false;', "new": 'if (acceptedTriggerIds.size > 0) return false;', "cmd": ["npx", "playwright", "test", "e2e/qoder-ack-rendered.spec.ts", "--config=playwright.config.ts", "--grep", "UNRELATED"]},
    {"id": "J-PROVENANCE-LAUNDER", "path": "backend/app/replanning/provider_snapshots.py", "old": 'if prov == "LIVE_CAPTURE":', "new": 'if prov:', "cmd": pytest("tests/test_qoder_mobility_truth_contract.py", "-k v6")},
    {"id": "J-NONE-QUALITY-HARD", "path": "backend/app/replanning/provider_snapshots.py", "old": 'if fact.fact_quality not in HARD_FEASIBLE_QUALITIES:', "new": 'if fact.fact_quality is None:', "cmd": pytest("tests/test_qoder_mobility_truth_contract.py", "-k hard_minutes")},
    {"id": "J-MOCK-HARD-FALLBACK", "path": "backend/app/integrations/mobility/runtime.py", "old": 'fallback=None if hard_capture else mock,', "new": 'fallback=mock,', "cmd": pytest("D:/moodle/_codex_sol_extreme_v2_20260919/tests/test_mutation_survivor_regressions.py", "-k hard_live")},
    {"id": "J-NONE-NONE-PHYSICAL", "path": "backend/app/replanning/mock_replan_engine.py", "old": 'if (\n        left_identity.row_id\n        and right_identity.row_id\n        and left_identity.row_id == right_identity.row_id\n    ):', "new": 'if left_identity.row_id == right_identity.row_id:', "cmd": pytest("tests/test_qoder_physical_identity_contract.py", "-k null_ids")},
    {"id": "J-COORDINATE-ONLY-SAME", "path": "backend/app/replanning/mock_replan_engine.py", "old": 'if left_name and right_name:', "new": 'if True:', "cmd": pytest("tests/test_qoder_physical_identity_contract.py", "-k coordinate_only")},
    {"id": "J-CROSS-PROVIDER-NUMERIC", "path": "backend/app/replanning/mock_replan_engine.py", "old": 'if left_scoped == right_scoped:', "new": 'if left_scoped[2] == right_scoped[2]:', "cmd": pytest("tests/test_qoder_physical_identity_contract.py", "-k provider")},
    {"id": "J-AMBIGUOUS-ADMITTED", "path": "backend/app/replanning/mock_replan_engine.py", "old": 'return compare_physical_venue(candidate, reference) != DIFFERENT', "new": 'return compare_physical_venue(candidate, reference) == SAME', "cmd": pytest("tests/test_qoder_physical_identity_contract.py", "-k ambiguous")},
    {"id": "J-PROTECTED-C4-DROPPED", "path": "backend/app/main.py", "old": 'active_c4_commitments = session.scalars(\n        select(CommitmentModel).where(\n            CommitmentModel.journey_id == journey.id,\n            CommitmentModel.status == "ACTIVE",\n            CommitmentModel.level == "C4_Anchored",', "new": 'active_c4_commitments = session.scalars(\n        select(CommitmentModel).where(\n            CommitmentModel.journey_id == journey.id,\n            CommitmentModel.status == "ACTIVE",\n            CommitmentModel.level == "C3_Guaranteed",', "cmd": pytest("D:/moodle/_codex_sol_extreme_v2_20260919/tests/test_extreme_real_api.py", "-k protected")},
    {"id": "J-PARTIAL-BUDGET-FULL", "path": "frontend/src/lib/budgetEvidence.ts", "old": 'state = knownCount === totalCount && verifiedCount === totalCount ? "FULL" : "PARTIAL";', "new": 'state = "FULL";', "cmd": ["npx", "playwright", "test", "e2e/qoder-budget-evidence.spec.ts", "--config=playwright.config.ts", "--grep", "PARTIAL"]},
    {"id": "J-LIVE-FIXED-INDEX", "path": "frontend/src/app/V8Experience.tsx", "old": 'const cursor =\n    plan.current_activity_id == null\n      ? plan.activities.findIndex((item) => !terminalStatuses.has(item.status))\n      : plan.activities.findIndex((item) => item.id === plan.current_activity_id);', "new": 'const cursor =\n    plan.current_activity_id == null\n      ? 0\n      : plan.activities.findIndex((item) => item.id === plan.current_activity_id);', "cmd": ["npx", "playwright", "test", "e2e/extreme-live-projection.spec.ts", "--config=playwright.extreme.config.ts"]},
    {"id": "J-STALE-CURSOR-FALLBACK", "path": "backend/app/operations/v9.py", "old": 'elif stale_cursor:', "new": 'elif False:', "cmd": pytest("D:/moodle/_codex_sol_extreme_v2_20260919/tests/test_extreme_real_api.py", "-k present_but_unknown")},
    {"id": "J-MATERIALITY-DIFF", "path": "backend/app/intelligence/replan_diff.py", "old": 'if before.start_at == after.start_at and before.end_at == after.end_at:', "new": 'if True:', "cmd": pytest("tests/test_foundation_replan_diff.py")},
    {"id": "J-C4-AMBIGUITY-FIRST", "path": "backend/app/commerce/service_impl.py", "old": 'if len(matches) == 1:\n        commitment.activity_id = matches[0].id\n        return\n    if len(matches) > 1:', "new": 'if matches:\n        commitment.activity_id = matches[0].id\n        return\n    if len(matches) > 1:', "cmd": pytest("tests/test_sol_v2_closeout.py", "-k ambiguous")},
    {"id": "J-C4-GENERIC-OVER-SEMANTIC", "path": "backend/app/commerce/service_impl.py", "old": 'if generic_wanted.intersection(candidate_generic) and not (\n            strong_wanted and candidate_strong\n        ):', "new": 'if generic_wanted.intersection(candidate_generic):', "cmd": pytest("tests/test_sol_v2_closeout.py", "-k different_semantics")},
]


def run(spec: dict) -> dict:
    path = ROOT / spec["path"]
    original = path.read_text(encoding="utf-8")
    if spec["old"] not in original:
        return {"id": spec["id"], "status": "NOT_APPLIED", "reason": "exact target not found"}
    mutated = original.replace(spec["old"], spec["new"], 1)
    path.write_text(mutated, encoding="utf-8")
    try:
        env = dict(os.environ)
        env["PYTHONPATH"] = str(BACKEND)
        cwd = ROOT / "frontend" if str(spec["cmd"][0]).startswith("npx") else BACKEND
        command = list(spec["cmd"])
        if command and command[0] == "npx":
            command[0] = "npx.cmd"
        proc = subprocess.run(
            command,
            cwd=cwd,
            env=env,
            text=True,
            encoding="utf-8",
            errors="replace",
            capture_output=True,
            timeout=180,
        )
        return {
            "id": spec["id"],
            "status": "KILLED" if proc.returncode == 1 else "SURVIVED" if proc.returncode == 0 else "ERROR",
            "exit_code": proc.returncode,
            "gate": " ".join(command),
            "evidence": ((proc.stdout or "") + (proc.stderr or ""))[-4000:],
            "diff": {"path": spec["path"], "old": spec["old"], "new": spec["new"]},
        }
    finally:
        path.write_text(original, encoding="utf-8")


def main() -> int:
    results = [run(item) for item in MUTANTS]
    OUT.write_text(json.dumps({"mutant_count": len(results), "results": results}, indent=2) + "\n", encoding="utf-8")
    for item in results:
        print(item["id"], item["status"])
    return 0 if all(item["status"] == "KILLED" for item in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
