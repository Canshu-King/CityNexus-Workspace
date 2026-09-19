from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def test_c4_freeze_uses_both_calibrations():
    src=(ROOT/"calibration"/"validate_c4_freeze.py").read_text(encoding="utf-8")
    assert "C4F_SemanticOverlay-report.json" in src
    assert "C4E1_ExtendFallback-report.json" in src
    assert "presentationEndpointTangentRatio" in src
def test_freeze_script_sets_c4_frozen():
    src=(ROOT/"calibration"/"freeze_c4.py").read_text(encoding="utf-8")
    assert 'summary.update({' in src
    assert '"C4":"FROZEN_PASS"' in src
    assert "P1_UC_OVERVIEW_ROUTE_PLAN" in src
