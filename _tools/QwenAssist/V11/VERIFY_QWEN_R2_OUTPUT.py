from __future__ import annotations

import ast
import csv
import sys
from pathlib import Path

root = Path(sys.argv[1] if len(sys.argv) > 1 else r"D:\moodle\CityNexus-QwenAssist\V11-R2")

errors: list[str] = []
warnings: list[str] = []

if not root.exists():
    raise SystemExit(f"Output root does not exist: {root}")

# Python candidate validation
py_files = list(root.rglob("*.py"))
candidate_tests = [p for p in py_files if "candidate_tests" in p.parts]
test_count = 0

for path in candidate_tests:
    text = path.read_text(encoding="utf-8", errors="replace")
    try:
        tree = ast.parse(text)
    except SyntaxError as exc:
        errors.append(f"SYNTAX {path}: {exc}")
        continue

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name.startswith("test_"):
            test_count += 1

    if "TODO" in text:
        errors.append(f"TODO placeholder in {path}")

    for node in ast.walk(tree):
        if isinstance(node, ast.Pass):
            # permit pass only in empty protocol/abstract scaffolding outside candidate_tests; here it is not accepted
            errors.append(f"PASS placeholder in {path}:{getattr(node, 'lineno', '?')}")
        if isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant) and node.value.value is Ellipsis:
            errors.append(f"ELLIPSIS placeholder in {path}:{getattr(node, 'lineno', '?')}")

if test_count < 25:
    errors.append(f"Only {test_count} candidate test functions; need >=25")

# Edge CSV
edge = root / "product" / "REAL_TRAVEL_EDGE_CASES.csv"
if not edge.exists():
    errors.append("Missing product/REAL_TRAVEL_EDGE_CASES.csv")
else:
    with edge.open("r", encoding="utf-8-sig", newline="") as fh:
        reader = csv.reader(fh)
        rows = list(reader)
    if not rows:
        errors.append("Edge-case CSV is empty")
    else:
        header = rows[0]
        if len(header) != 8:
            errors.append(f"Edge-case CSV header has {len(header)} cols, expected 8")
        body = rows[1:]
        if len(body) < 150:
            errors.append(f"Edge-case CSV has {len(body)} rows, expected >=150")
        ids = []
        for idx, row in enumerate(body, start=2):
            if len(row) != 8:
                errors.append(f"Edge-case CSV row {idx} has {len(row)} cols")
                continue
            ids.append(row[0])
            if not row[0].strip():
                errors.append(f"Edge-case CSV row {idx} missing ID")
            if not row[7].strip():
                errors.append(f"Edge-case CSV row {idx} missing Priority")
        if len(ids) != len(set(ids)):
            errors.append("Edge-case CSV has duplicate IDs")

# Required round-2 outputs
required = [
    "providers/OPENING_HOURS_IMPLEMENTATION_NOTES.md",
    "providers/GTFS_QUALITY_PIPELINE.md",
    "web/SOURCEFUL_SEARCH_PROVIDER_DESIGN.md",
    "web/WEB_TRUST_ADVERSARIAL_CASES.md",
    "providers/SEALED_CAPTURE_SPEC.md",
    "providers/PROVENANCE_TEST_MATRIX.csv",
    "frontend/DND_TRIP_STUDIO_INTERACTION.md",
    "frontend/GITHUB_UI_ADOPTION_RESEARCH_R2.md",
    "frontend/GITHUB_ADOPTION_STATUS.csv",
    "frontend/HANDWRITTEN_TYPE_DUPLICATES.csv",
    "frontend/DIRECT_API_CALLS.csv",
    "frontend/STORYBOOK_MATRIX_R2.csv",
    "QWEN_HANDOFF_TO_CODEX_R2.md",
]

for rel in required:
    if not (root / rel).exists():
        errors.append(f"Missing required output: {rel}")

# P0 no TBD
p0 = root / "analysis" / "P0_CODE_LOCATION_MAP_R2.md"
if not p0.exists():
    warnings.append("Missing analysis/P0_CODE_LOCATION_MAP_R2.md")
else:
    text = p0.read_text(encoding="utf-8", errors="replace")
    if "TBD" in text:
        errors.append("P0_CODE_LOCATION_MAP_R2.md still contains TBD")

print(f"Candidate tests: {test_count}")
print(f"Errors: {len(errors)}")
for item in errors:
    print("ERROR:", item)
print(f"Warnings: {len(warnings)}")
for item in warnings:
    print("WARN:", item)

raise SystemExit(1 if errors else 0)
