#!/usr/bin/env python3
"""Build a lightweight symbol-level overlap map from Git ranges."""
from __future__ import annotations

import argparse
import ast
import json
import re
import subprocess
from pathlib import Path

RANGES = {
    "truth": "380e6ff..b12f24f",
    "visual_ia": "b12f24f..e330ac2",
    "prerequisites": "e330ac2..a2124c0",
    "evidence": "a2124c0..1de4e0c",
}


def git(repo: Path, *args: str) -> str:
    return subprocess.check_output(["git", "-C", str(repo), *args], text=True, encoding="utf-8", errors="replace")


def symbols(path: str, text: str) -> list[str]:
    if path.endswith(".py"):
        try:
            tree = ast.parse(text)
            return sorted({node.name for node in ast.walk(tree) if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))})
        except SyntaxError:
            return []
    if path.endswith((".ts", ".tsx")):
        pattern = r"(?:export\s+)?(?:async\s+)?(?:function|class|const|type|interface)\s+([A-Za-z_$][\w$]*)"
        return sorted(set(re.findall(pattern, text)))
    return []


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("repo", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    owners: dict[str, list[str]] = {}
    for owner, range_spec in RANGES.items():
        for line in git(args.repo, "diff", "--name-only", range_spec).splitlines():
            owners.setdefault(line, []).append(owner)
    rows = []
    for path, changed_by in sorted(owners.items()):
        if len(changed_by) < 2:
            continue
        try:
            content = git(args.repo, "show", f"1de4e0c:{path}")
        except subprocess.CalledProcessError:
            content = ""
        rows.append({"file": path, "changed_by": changed_by, "current_symbols": symbols(path, content)})
    result = {"snapshot": "1de4e0c", "ranges": RANGES, "overlaps": rows}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"overlap_files": len(rows), "output": str(args.output)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
