#!/usr/bin/env python3
"""
Read-only SQLite target preflight for CityNexus probes.

Goal: prove which database a probe is actually about to inspect before anyone
writes conclusions such as 'no rows changed' or 'this is an isolated DB'.

IMPORTANT:
- Pass the database URL that the running app actually resolved, e.g.
  app.settings.database_url. Do not pass an assumed environment variable value.
- This tool never creates a database. SQLite is opened in mode=ro.
"""

from __future__ import annotations

import argparse
import json
import os
import sqlite3
from pathlib import Path
from urllib.parse import quote


KNOWN_COUNT_TABLES = (
    "journeys",
    "plan_versions",
    "travelers",
    "catalog_hydration_operations",
)


def sqlite_path_from_url(url: str, cwd: Path) -> Path:
    prefixes = ("sqlite:///", "sqlite+pysqlite:///")
    prefix = next((p for p in prefixes if url.startswith(p)), None)
    if prefix is None:
        raise SystemExit("UNSUPPORTED_DATABASE_URL: expected sqlite:/// or sqlite+pysqlite:///")

    raw = url[len(prefix):]
    if raw == ":memory:":
        raise SystemExit("MEMORY_DATABASE_UNINSPECTABLE: no durable file target")

    # SQLAlchemy sqlite:///./x.db is relative to process CWD.
    p = Path(raw)
    if not p.is_absolute():
        p = cwd / p
    return p.resolve()


def qident(name: str) -> str:
    return '"' + name.replace('"', '""') + '"'


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--database-url", required=True, help="value actually resolved by the app")
    ap.add_argument("--cwd", default=os.getcwd(), help="actual process working directory")
    ap.add_argument("--source-label", default="app.settings.database_url")
    ap.add_argument("--expected-min-tables", type=int, default=1)
    args = ap.parse_args()

    cwd = Path(args.cwd).resolve()
    db_path = sqlite_path_from_url(args.database_url, cwd)

    receipt = {
        "source_label": args.source_label,
        "database_url_as_resolved_by_app": args.database_url,
        "process_cwd": str(cwd),
        "resolved_database_path": str(db_path),
        "exists_before_open": db_path.exists(),
        "open_mode": "sqlite mode=ro",
    }

    if not db_path.exists():
        receipt.update({
            "status": "TARGET_MISSING",
            "safe_to_claim_clean": False,
            "reason": "Resolved SQLite file does not exist; refusing to create it or infer a clean state.",
        })
        print(json.dumps(receipt, ensure_ascii=False, indent=2))
        return 2

    # URI mode=ro prevents accidental file creation/mutation.
    uri = f"file:{quote(str(db_path))}?mode=ro"
    try:
        con = sqlite3.connect(uri, uri=True)
    except sqlite3.Error as exc:
        receipt.update({
            "status": "READ_ONLY_OPEN_FAILED",
            "safe_to_claim_clean": False,
            "error": repr(exc),
        })
        print(json.dumps(receipt, ensure_ascii=False, indent=2))
        return 3

    try:
        tables = [
            row[0]
            for row in con.execute(
                "SELECT name FROM sqlite_master "
                "WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
            )
        ]
        counts = {}
        for name in KNOWN_COUNT_TABLES:
            if name in tables:
                counts[name] = con.execute(f"SELECT COUNT(*) FROM {qident(name)}").fetchone()[0]

        receipt.update({
            "table_count": len(tables),
            "tables": tables,
            "known_table_counts": counts,
        })

        if len(tables) < args.expected_min_tables:
            receipt.update({
                "status": "EMPTY_OR_WRONG_OBSERVATION_SURFACE",
                "safe_to_claim_clean": False,
                "reason": "Observed fewer tables than expected; empty inventory is UNKNOWN/UNMEASURED, not CLEAN.",
            })
            rc = 4
        else:
            receipt.update({
                "status": "READ_ONLY_TARGET_IDENTIFIED",
                "safe_to_claim_clean": True,
                "reason": "Target identity and non-empty schema were observed read-only. This does not itself prove application isolation.",
            })
            rc = 0
    finally:
        con.close()

    print(json.dumps(receipt, ensure_ascii=False, indent=2))
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
