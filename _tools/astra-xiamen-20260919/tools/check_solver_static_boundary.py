from __future__ import annotations

import ast
from pathlib import Path
import sys

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
FILES = [
    ROOT / "app/planning/solver_contract.py",
    ROOT / "app/planning/reference_replan_solver.py",
    ROOT / "app/planning/ortools_replan_solver.py",
    ROOT / "app/planning/solver_runtime.py",
]
FORBIDDEN_PREFIXES = (
    "fastapi",
    "sqlalchemy",
    "httpx",
    "requests",
    "urllib",
    "aiohttp",
    "app.db",
    "app.models",
    "app.integrations",
)

failures: list[str] = []
checked = 0
for path in FILES:
    if not path.exists():
        continue
    checked += 1
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for node in ast.walk(tree):
        modules: list[str] = []
        if isinstance(node, ast.Import):
            modules.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules.append(node.module)
        for module in modules:
            if module.startswith(FORBIDDEN_PREFIXES):
                failures.append(f"{path.relative_to(ROOT)} imports forbidden runtime dependency {module}")

if checked == 0:
    print("FAIL: no solver modules found")
    raise SystemExit(1)
if failures:
    print("SOLVER STATIC BOUNDARY FAIL")
    for failure in failures:
        print(f"- {failure}")
    raise SystemExit(1)
print(f"SOLVER STATIC BOUNDARY PASS ({checked} modules checked)")


