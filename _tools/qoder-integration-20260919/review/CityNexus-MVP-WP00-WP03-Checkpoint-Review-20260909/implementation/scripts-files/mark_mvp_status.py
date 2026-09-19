"""Apply evidence-backed WP01-WP03 statuses to the imported ledger."""

from __future__ import annotations

import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "docs" / "implementation" / "implementation-status.csv"

UPDATES = {
    "BG-002": (
        "PARTIAL",
        "backend/tests/test_wp01_wp03.py",
        "CNX-I-003;CNX-I-005;CNX-I-009;CNX-I-010",
    ),
    "BG-006": ("SIMULATED", "data/mock/city_services.json", "CNX-I-008"),
    "FR-001": ("PARTIAL", "backend/app/main.py", "CNX-I-003"),
    "FR-002": ("PARTIAL", "backend/app/main.py", "CNX-I-004"),
    "FR-006": ("IMPLEMENTED", "backend/app/main.py", "CNX-I-005"),
    "FR-007": ("PARTIAL", "backend/app/main.py", "CNX-I-005"),
    "FR-010": (
        "PARTIAL",
        "backend/app/services.py",
        "CNX-I-009;CNX-U-001;CNX-U-006;CNX-U-007;CNX-U-008",
    ),
    "FR-011": ("PARTIAL", "backend/app/schemas.py", "CNX-U-019;CNX-U-020"),
    "FR-018": ("IMPLEMENTED", "backend/app/main.py", "CNX-I-008"),
    "FR-019": ("SIMULATED", "backend/app/integrations/mock/providers.py", "CNX-I-008"),
    "FR-020": ("PARTIAL", "backend/app/main.py", "CNX-I-008"),
    "FR-021": ("SIMULATED", "backend/app/main.py", "CNX-I-008"),
    "FR-022": ("SIMULATED", "data/mock/city_services.json", "CNX-I-008"),
    "FR-024": ("PARTIAL", "backend/app/services.py", "CNX-U-006;CNX-U-007;CNX-U-008"),
    "FR-025": ("PARTIAL", "backend/app/services.py", "CNX-U-001;CNX-U-002;CNX-I-009"),
    "BR-005": ("SIMULATED", "backend/app/integrations/mock/providers.py", "CNX-I-008"),
    "BR-008": ("PARTIAL", "backend/app/services.py", "CNX-U-006;CNX-U-007;CNX-U-008"),
    "BR-019": ("IMPLEMENTED", "backend/app/replanning/reference_replanner.py", "CNX-U-006"),
    "BR-020": ("SIMULATED", "backend/app/integrations/mock/providers.py", "CNX-C-005"),
    "IR-001": ("SIMULATED", "backend/app/integrations/mock/providers.py", "CNX-C-001;CNX-I-008"),
    "IR-003": ("SIMULATED", "backend/app/integrations/mock/providers.py", "CNX-C-005"),
    "IR-011": ("PARTIAL", "backend/app/replanning/reference_replanner.py", "CNX-U-001;CNX-U-010"),
    "IR-012": ("SIMULATED", "backend/app/integrations/mock/providers.py", "CNX-C-005"),
    "NFR-013": ("PARTIAL", "backend/app/main.py", "CNX-I-003;CNX-I-005;CNX-I-009"),
}


def main() -> None:
    with LEDGER.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)
        fieldnames = reader.fieldnames or []
    for row in rows:
        if row["requirement_id"] in UPDATES:
            status, evidence, tests = UPDATES[row["requirement_id"]]
            row["implementation_status"] = status
            row["evidence"] = evidence
            row["test_ids"] = tests
            row["notes"] = (
                "WP01-WP03 evidence linked; deferred acceptance criteria remain explicitly partial/simulated."
            )
    with LEDGER.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(f"Updated {sum(row['requirement_id'] in UPDATES for row in rows)} requirement statuses")


if __name__ == "__main__":
    main()
