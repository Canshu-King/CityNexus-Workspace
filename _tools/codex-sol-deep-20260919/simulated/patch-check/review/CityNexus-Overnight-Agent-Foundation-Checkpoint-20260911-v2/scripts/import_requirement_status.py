"""Import the frozen requirements baseline into the implementation ledger.

The source wording is serialized as JSON in the CSV fields so importing the
ledger never rewrites or paraphrases the requirements baseline.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "requirements" / "requirements.yaml"
OUTPUT = ROOT / "docs" / "implementation" / "implementation-status.csv"


def json_cell(value: object) -> str:
    return json.dumps(
        value if value is not None else [], ensure_ascii=False, separators=(",", ":")
    )


def main() -> None:
    baseline = yaml.safe_load(SOURCE.read_text(encoding="utf-8"))
    rows: list[dict[str, str]] = []
    for section, items in baseline.items():
        if not isinstance(items, list) or section == "metadata":
            continue
        for item in items:
            if not isinstance(item, dict) or "id" not in item:
                continue
            domain = item.get("domainElements") or []
            trace = {
                "use_cases": item.get("useCases") or [],
                "domain_elements": domain,
                "depends_on": item.get("dependsOn") or [],
            }
            rows.append(
                {
                    "requirement_id": str(item["id"]),
                    "type": str(
                        item.get("type", section.removesuffix("_requirements").upper())
                    ),
                    "summary": str(item.get("title", "")),
                    "source": "requirements/requirements.yaml",
                    "priority": str(item.get("priority", "")),
                    "acceptance_criteria": json_cell(
                        item.get("acceptanceCriteria") or []
                    ),
                    "trace_links": json_cell(trace),
                    "implementation_status": "PLANNED",
                    "evidence": "",
                    "test_ids": ";".join(str(x) for x in (item.get("testCases") or [])),
                    "owner": "",
                    "notes": "Imported from frozen baseline; status requires implementation evidence.",
                }
            )
    rows.sort(key=lambda row: row["requirement_id"])
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print(f"Imported {len(rows)} requirements into {OUTPUT}")


if __name__ == "__main__":
    main()
