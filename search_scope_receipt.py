#!/usr/bin/env python3
"""
Fail-closed search-scope receipt for negative assertions.

Use before writing claims such as "not present", "0 consumers", "not delivered",
or "no implementation". The tool records WHERE and HOW the search was run and
requires at least one broadened search pass before a negative verdict can be
emitted.

This is a control-plane utility. It does not decide product behavior.
"""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path


def run(cmd: list[str], cwd: Path) -> tuple[int, str, str]:
    p = subprocess.run(
        cmd,
        cwd=str(cwd),
        text=True,
        capture_output=True,
        encoding="utf-8",
        errors="replace",
    )
    return p.returncode, p.stdout, p.stderr


def git_ref(root: Path) -> str:
    rc, out, err = run(["git", "rev-parse", "HEAD"], root)
    if rc != 0:
        raise RuntimeError(f"GIT_REF_FAILED: {err.strip()}")
    return out.strip()


def git_toplevel(root: Path) -> str:
    rc, out, err = run(["git", "rev-parse", "--show-toplevel"], root)
    if rc != 0:
        raise RuntimeError(f"GIT_TOPLEVEL_FAILED: {err.strip()}")
    return out.strip()


def git_grep(root: Path, pattern: str, paths: list[str]) -> dict:
    cmd = ["git", "grep", "-n", "-E", pattern, "HEAD", "--"]
    cmd.extend(paths or ["."])
    rc, out, err = run(cmd, root)

    # git grep: 0=matches, 1=no matches, >1=error
    if rc not in (0, 1):
        raise RuntimeError(
            f"SEARCH_EXECUTION_FAILED pattern={pattern!r}: {err.strip()}"
        )

    matches = [line for line in out.splitlines() if line.strip()]
    return {
        "pattern": pattern,
        "paths": paths or ["."],
        "returncode": rc,
        "match_count": len(matches),
        "matches": matches,
    }


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--root", required=True, type=Path)
    p.add_argument("--scope-label", required=True)
    p.add_argument("--pattern", required=True)
    p.add_argument(
        "--broaden-pattern",
        action="append",
        default=[],
        help="Required for a negative verdict. Repeat for synonym/import/directory-level searches.",
    )
    p.add_argument(
        "--path",
        action="append",
        default=[],
        help="Limit search to a path. Repeat as needed. Defaults to repository root.",
    )
    args = p.parse_args()

    root = args.root.resolve()
    if not root.exists():
        raise RuntimeError(f"ROOT_NOT_FOUND: {root}")

    repo_root = git_toplevel(root)
    ref = git_ref(root)

    primary = git_grep(root, args.pattern, args.path)
    broadened = [
        git_grep(root, pattern, args.path)
        for pattern in args.broaden_pattern
    ]

    any_match = primary["match_count"] > 0 or any(
        x["match_count"] > 0 for x in broadened
    )

    if primary["match_count"] == 0 and not broadened:
        verdict = "INCOMPLETE_NEGATIVE_ASSERTION"
        reason = "Primary search found zero matches, but no broadened pass was supplied."
    elif any_match:
        verdict = "PRESENCE_OBSERVED"
        reason = "At least one declared search pass found matching material."
    else:
        verdict = "ABSENT_IN_DECLARED_SCOPE"
        reason = (
            "No declared search pass found a match. This verdict applies only to the "
            "recorded repository/worktree/ref/paths and must not be generalized to "
            "other worktrees, branches, repositories, uncommitted changes, or runtime behavior."
        )

    receipt = {
        "scope_label": args.scope_label,
        "repository_root": repo_root,
        "search_root": str(root),
        "ref": ref,
        "paths": args.path or ["."],
        "primary_search": primary,
        "broadened_searches": broadened,
        "verdict": verdict,
        "reason": reason,
        "negative_claim_allowed": verdict == "ABSENT_IN_DECLARED_SCOPE",
        "frozen_rule": (
            "Absence is scoped evidence. A clean authoritative tree does not prove "
            "a feature was never delivered in another lane/worktree."
        ),
    }

    print(json.dumps(receipt, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
