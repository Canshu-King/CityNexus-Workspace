from pathlib import Path
import sys
import pytest

ROOT = Path(__file__).resolve().parents[1]
CAL = ROOT / "calibration"
sys.path.insert(0, str(CAL))

from audit_p1_route_topology_v2 import TopologyGateError, require_planar_topology

SEM = ROOT.parent / "visio-spec" / "pages" / "p1_uc_overview.yaml"
CAND = ROOT / "phase1-routing-rc6-candidate.yaml"
PLANS = CAL / "P1_ROUTE_PORT_PLANS.yaml"


def test_known_planar_seed_passes_runtime_gate():
    payload = require_planar_topology(
        semantic=SEM, candidate=CAND, plans=PLANS,
        plan="PLAN_TRAVELER_SKELETON_PLANAR_GRID",
    )
    assert payload["status"] == "PASS"
    assert payload["orientableGenus"] == 0


def test_known_nonplanar_seed_is_rejected_before_routing():
    with pytest.raises(TopologyGateError) as exc:
        require_planar_topology(
            semantic=SEM, candidate=CAND, plans=PLANS,
            plan="PLAN_TRAVELER_SKELETON_PROVIDER_GRID",
        )
    assert exc.value.payload["orientableGenus"] == 1


def test_negotiated_loader_contains_central_topology_interlock():
    src = (CAL / "route_p1_negotiated_grid.py").read_text(encoding="utf-8")
    assert "topology_gate(plan_id)" in src
    assert "require_planar_topology" in src


def test_shared_solver_loader_rejects_nonplanar_plan():
    from route_p1_negotiated_grid import load
    with pytest.raises(TopologyGateError):
        load("PLAN_TRAVELER_SKELETON_PROVIDER_GRID")
