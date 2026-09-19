from __future__ import annotations

from pathlib import Path
import re
import sys

root = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()

def read(rel: str) -> str:
    p = root / rel
    return p.read_text(encoding="utf-8", errors="replace") if p.exists() else ""

main = read("backend/app/main.py")
services = read("backend/app/services.py")
models = read("backend/app/db/models.py")
ops = read("backend/app/operations/v9.py")
v8 = read("frontend/src/app/V8Experience.tsx")
map_panel = read("frontend/src/components/v8/MapPanel.tsx")
pkg = read("frontend/package.json")
api = read("frontend/src/api/v10Execution.ts")

checks: list[tuple[str, bool]] = []

# Selection endpoint should no longer recapture provider evidence.
select_start = main.find('def select_plan(')
select_end = main.find('@app.', select_start + 1) if select_start >= 0 else -1
select_block = main[select_start:select_end if select_end > select_start else None]

checks.append((
    "P0-01 selection gate does not recapture runtime mobility",
    "capture_runtime_mobility_snapshot" not in select_block,
))

checks.append((
    "P0-02 PlanVersion has a durable mobility/provider evidence reference",
    any(token in models for token in (
        "mobility_snapshot_id",
        "mobility_evidence_id",
        "provider_snapshot_id",
        "frozen_evidence_id",
    )),
))

checks.append((
    "P0-03 Generic Compose does not merely iterate selected_ids in final order",
    "for place_id in selected_ids:" not in services[
        services.find("def _generic_compose_plans"):services.find("\ndef ", services.find("def _generic_compose_plans") + 10)
        if services.find("\ndef ", services.find("def _generic_compose_plans") + 10) > 0 else None
    ],
))

checks.append((
    "P0-04 DnD no longer stops at console.info pending-feasibility",
    'impact: "pending-feasibility"' not in v8 and "console.info(\"trip-studio draft preview\"" not in v8,
))

checks.append((
    "P0-05 MapLibre resize lifecycle exists",
    "ResizeObserver" in map_panel or ".resize()" in map_panel,
))

checks.append((
    "P0-06 frontend uses MSW or equivalent state-fixture tooling for UI states",
    "\"msw\"" in pkg or "@mswjs" in pkg,
))

checks.append((
    "P0-07 V12 API surface is not adding more duplicate hand-written WebObservation shape",
    "type WebObservation =" not in api and "interface WebObservation" not in api,
))

checks.append((
    "P0-08 execution states include EN_ROUTE and ARRIVED and IN_PROGRESS",
    all(token in (models + ops) for token in ("EN_ROUTE", "ARRIVED", "IN_PROGRESS")),
))

checks.append((
    "P0-09 unknown reservation money does not blindly materialize using int(price or 0)",
    "int(price or 0)" not in ops,
))

failed = [name for name, ok in checks if not ok]
for name, ok in checks:
    print(("PASS " if ok else "FAIL ") + name)

print(f"\nSummary: {len(checks)-len(failed)} passed / {len(failed)} failed")
raise SystemExit(1 if failed else 0)
