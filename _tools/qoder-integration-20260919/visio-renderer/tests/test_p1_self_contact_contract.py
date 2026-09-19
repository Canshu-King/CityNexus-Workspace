from pathlib import Path
import sys
import pytest

ROOT = Path(__file__).resolve().parents[1]
CAL = ROOT / "calibration"
sys.path.insert(0, str(CAL))

from route_candidate_selector import CandidateError, make_candidate


def test_candidate_rejects_nonadjacent_self_crossing():
    with pytest.raises(CandidateError):
        make_candidate({
            "routeId": "R", "family": "test", "cost": 1,
            "points": [[0, 0], [2, 0], [2, 2], [1, 2], [1, -1]],
        })


def test_candidate_rejects_self_retrace_overlap():
    with pytest.raises(CandidateError):
        make_candidate({
            "routeId": "R", "family": "test", "cost": 1,
            "points": [[0, 0], [2, 0], [2, 1], [1, 1], [1, 0], [3, 0]],
        })


def test_contact_audit_has_self_contact_gate():
    src = (CAL / "audit_p1_route_contacts.py").read_text(encoding="utf-8")
    assert "selfContactCount" in src
    assert "selfContacts" in src
    assert "self-route contacts" in src


def test_candidate_pool_has_no_hardcoded_handoff_dependency():
    src = (CAL / "explore_p1_disjoint_pool.py").read_text(encoding="utf-8")
    assert "handoff_20260907" not in src
    assert "--traveler-skeleton" in src
    assert "bestObservedDisjointSubset" in src
    assert "maximalDisjointSubset" not in src


def test_pair_compatibility_precheck_can_prove_current_pool_impossible():
    from route_candidate_selector import route_pair_compatibility
    a = make_candidate({"routeId":"A","family":"x","cost":1,"points":[[0,0],[2,0]]})
    b = make_candidate({"routeId":"B","family":"x","cost":1,"points":[[1,-1],[1,1]]})
    rows = route_pair_compatibility({"A":[a],"B":[b]})
    assert rows[0]["compatiblePairs"] == 0
    assert rows[0]["compatibilityRatio"] == 0


def test_no_solver_depends_on_handoff_20260907_path():
    for name in ("explore_p1_disjoint_pool.py", "search_planar_skeleton_ports.py", "prepare_p1_corridors.py"):
        src = (CAL / name).read_text(encoding="utf-8")
        assert "handoff_20260907" not in src


def test_negotiated_router_has_exact_pre_staging_contact_check():
    src = (CAL / "route_p1_negotiated_grid.py").read_text(encoding="utf-8")
    assert "def exact_path_conflicts" in src
    assert 'not exact["selfFailures"]' in src
    assert 'not exact["crossRoutePairs"]' in src
