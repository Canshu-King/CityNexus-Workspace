"""Hardened P1 route candidate gate.

Runs the historical semantic/orthogonal/node/page checks, then adds the missing
cross-route contact audit.  A formal route plan cannot pass while unrelated
connectors meet at T-junctions or shared intermediate waypoints.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "out"
BASE_REPORT = OUT / "P1_UC_ROUTE_CANDIDATE-report.json"
CONTACT_REPORT = OUT / "P1_UC_ROUTE_CONTACT-AUDIT.json"
REPORT = OUT / "P1_UC_ROUTE_CANDIDATE-v2-report.json"


def run(script: str):
    return subprocess.run([sys.executable, str(HERE / script)], check=False)


def main():
    base = run("validate_p1_route_candidate.py")
    contact = run("audit_p1_route_contacts.py")

    base_payload = json.loads(BASE_REPORT.read_text(encoding="utf-8"))
    contact_payload = json.loads(CONTACT_REPORT.read_text(encoding="utf-8"))

    failures = []
    if base.returncode != 0 or base_payload.get("status") != "PASS":
        failures.append("historical route gate failed")
    if contact.returncode != 0 or contact_payload.get("status") != "PASS":
        failures.extend(contact_payload.get("failures", ["contact audit failed"]))

    payload = {
        "pageName": base_payload.get("pageName"),
        "status": "PASS" if not failures else "FAIL",
        "baseGateStatus": base_payload.get("status"),
        "semanticConnectorCount": base_payload.get("semanticConnectorCount"),
        "candidateRouteCount": base_payload.get("candidateRouteCount"),
        "explicitGeometryRouteCount": base_payload.get("explicitGeometryRouteCount"),
        "properCrossingCount": base_payload.get("crossingCount"),
        "collinearOverlapPairCount": base_payload.get("overlapCount"),
        "contactPairCount": contact_payload.get("contactPairCount"),
        "uniqueContactCount": contact_payload.get("uniqueContactCount"),
        "contactCounts": contact_payload.get("contactCounts"),
        "shortSegmentCount": contact_payload.get("shortSegmentCount"),
        "redundantCollinearPointCount": contact_payload.get("redundantCollinearPointCount"),
        "failures": failures,
    }
    REPORT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=True, indent=2))
    return 0 if payload["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
