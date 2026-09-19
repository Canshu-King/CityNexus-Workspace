#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import sqlite3
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


def fail(message: str) -> None:
    raise AssertionError(message)


def load_json(path: Path):
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def main() -> int:
    checks: list[str] = []

    # YAML parse checks.
    openapi = yaml.safe_load((ROOT / "api/openapi.yaml").read_text(encoding="utf-8"))
    sm = yaml.safe_load((ROOT / "state-machines/state_machines.yaml").read_text(encoding="utf-8"))
    wp = yaml.safe_load((ROOT / "work-packages/work_packages.yaml").read_text(encoding="utf-8"))
    if openapi.get("openapi") != "3.1.0":
        fail("unexpected OpenAPI version")
    if len(openapi.get("paths", {})) < 20:
        fail("OpenAPI path coverage unexpectedly small")

    refs = []
    def collect_refs(obj):
        if isinstance(obj, dict):
            for k, v in obj.items():
                if k == "$ref" and isinstance(v, str):
                    refs.append(v)
                else:
                    collect_refs(v)
        elif isinstance(obj, list):
            for item in obj:
                collect_refs(item)
    collect_refs(openapi)
    for ref in refs:
        if not ref.startswith("#/components/"):
            continue
        node = openapi
        for part in ref[2:].split("/"):
            if not isinstance(node, dict) or part not in node:
                fail(f"unresolved OpenAPI ref: {ref}")
            node = node[part]
    checks.append(f"openapi_paths={len(openapi['paths'])}")
    checks.append(f"openapi_local_refs={len(refs)}")
    if "ReplanProposal" not in sm.get("machines", {}):
        fail("missing ReplanProposal state machine")
    checks.append(f"state_machines={len(sm['machines'])}")

    # SQLite schema executes cleanly.
    conn = sqlite3.connect(":memory:")
    conn.executescript((ROOT / "db/schema.sql").read_text(encoding="utf-8"))
    tables = {
        r[0]
        for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
        if not r[0].startswith("sqlite_")
    }
    expected_tables = {
        "travelers", "preferences", "journeys", "journey_twins", "constraints",
        "plan_versions", "activities", "places", "city_services", "commitments",
        "events", "replan_proposals", "bookings", "orders", "transactions",
        "recommendations", "provider_calls", "audit_logs", "idempotency_keys",
    }
    missing = expected_tables - tables
    if missing:
        fail(f"missing schema tables: {sorted(missing)}")
    checks.append(f"sqlite_tables={len(tables)}")

    # Mock referential integrity at fixture level.
    places = load_json(ROOT / "mock/places.json")
    place_ids = {p["id"] for p in places}
    if len(place_ids) != len(places):
        fail("duplicate mock place ids")
    services = load_json(ROOT / "mock/city_services.json")
    for s in services:
        if s.get("place_id") is not None and s["place_id"] not in place_ids:
            fail(f"service references unknown place: {s['id']}")
    events = load_json(ROOT / "mock/events.json")
    for e in events:
        affected = e.get("affected_place_id")
        if affected and affected not in place_ids:
            fail(f"event references unknown place: {affected}")
    demo = load_json(ROOT / "mock/demo_journey.json")
    for p in demo["expected_initial_places"]:
        if p not in place_ids:
            fail(f"demo journey references unknown place: {p}")
    if demo["locked_commitment"]["place_id"] not in place_ids:
        fail("locked commitment references unknown place")
    checks.append(f"mock_places={len(places)}")

    # Replanning weights from reference module.
    sys.path.insert(0, str(ROOT / "replanning"))
    import reference_replanner as rr  # type: ignore
    if abs(rr.weights_sum() - 1.0) > 1e-12:
        fail("replanning weights do not sum to 1.0")
    checks.append("replan_weights=1.0")

    # Test IDs unique.
    with (ROOT / "tests/test_matrix.csv").open("r", encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    ids = [r["test_id"] for r in rows]
    if len(ids) != len(set(ids)):
        fail("duplicate test ids")
    if not any(r["priority"] == "P0" for r in rows):
        fail("no P0 tests")
    checks.append(f"test_matrix_rows={len(rows)}")

    # Work-package dependencies only reference existing packages.
    packages = wp.get("packages", [])
    wp_ids = {p["id"] for p in packages}
    for p in packages:
        for dep in p.get("depends_on", []):
            if dep not in wp_ids:
                fail(f"unknown work package dependency: {p['id']} -> {dep}")
    checks.append(f"work_packages={len(packages)}")

    print("CityNexus blueprint validation PASS")
    for check in checks:
        print(f"- {check}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
