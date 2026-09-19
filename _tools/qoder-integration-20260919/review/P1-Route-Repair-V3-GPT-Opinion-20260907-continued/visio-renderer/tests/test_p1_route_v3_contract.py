from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_v3_composes_v2_and_protects_frozen_extend_geometry():
    src = (ROOT / "calibration" / "validate_p1_route_candidate_v3.py").read_text(encoding="utf-8")
    assert "validate_p1_route_candidate_v2.py" in src
    assert "EXT-07-06" in src
    assert "EXT-09-08" in src
    assert "EXT-10-09" in src
    assert "FROZEN_FROM_C4E1" in src
    assert "frozen Extend waypoints changed" in src


def test_v3_requires_final_status_only_after_geometry_pass():
    src = (ROOT / "calibration" / "validate_p1_route_candidate_v3.py").read_text(encoding="utf-8")
    assert 'if v2.get("status") == "PASS"' in src
    assert "GEOMETRY_PASS_PENDING_EXTERNAL_FREEZE" in src
    assert "ROUTE_PLANNED_PENDING_EXTERNAL_FREEZE" in src


def test_conflict_analyzer_ranks_frozen_extend_contacts_first():
    src = (ROOT / "calibration" / "analyze_p1_route_conflicts.py").read_text(encoding="utf-8")
    assert "100 * ext_contacts[route]" in src
    assert "repairOrder" in src
    assert "Do not repair contacts one-by-one with micro-jogs." in src
