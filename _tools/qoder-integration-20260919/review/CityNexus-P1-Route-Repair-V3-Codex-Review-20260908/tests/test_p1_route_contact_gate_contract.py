from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_contact_audit_covers_missing_intersection_classes():
    src = (ROOT / "calibration" / "audit_p1_route_contacts.py").read_text(encoding="utf-8")
    for token in ("tjunction", "shared_endpoint", "crossing", "overlap"):
        assert token in src
    assert "MIN_SEGMENT_CM = 0.10" in src
    assert "redundantCollinearPointCount" in src


def test_v2_gate_requires_contact_audit_pass():
    src = (ROOT / "calibration" / "validate_p1_route_candidate_v2.py").read_text(encoding="utf-8")
    assert "validate_p1_route_candidate.py" in src
    assert "audit_p1_route_contacts.py" in src
    assert "contactPairCount" in src
    assert 'payload["status"] == "PASS"' in src
