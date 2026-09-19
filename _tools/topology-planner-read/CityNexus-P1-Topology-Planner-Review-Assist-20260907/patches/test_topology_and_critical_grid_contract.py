from pathlib import Path
import importlib.util
import yaml

HERE = Path(__file__).resolve().parent


def _load_topology_module(name="topov2"):
    mod_path = HERE / "audit_p1_route_topology_v2.py"
    spec = importlib.util.spec_from_file_location(name, mod_path)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


def test_critical_grid_quantizes_known_off_grid_coordinates():
    from critical_grid_geometry import q, unq

    for value in (3.16, 4.23, 8.875, 11.225, 12.575):
        assert abs(unq(q(value)) - value) < 1e-9


def test_exact_contact_detects_off_grid_crossing():
    from critical_grid_geometry import q, closed_contact

    a = (q(20.0), q(3.16))
    b = (q(28.0), q(3.16))
    c = (q(26.0), q(2.0))
    d = (q(26.0), q(4.23))
    assert closed_contact(a, b, c, d)


def test_topology_auditor_declares_only_allowed_override_keys():
    mod = _load_topology_module()
    assert mod.ALLOWED_OVERRIDE_KEYS == {
        "sourcePortFraction",
        "targetSide",
        "targetPortFraction",
    }
    assert "EXT-07-06" in mod.FROZEN_EXTEND_IDS


def test_topology_load_plan_rejects_prohibited_identity_override(tmp_path):
    mod = _load_topology_module("topov2_identity")
    plan = tmp_path / "bad.yaml"
    plan.write_text(
        yaml.safe_dump(
            {"plans": {"BAD": {"routes": {"A1": {"source": "OTHER"}}}}}
        ),
        encoding="utf-8",
    )
    overrides, failures = mod.load_plan(
        plan,
        "BAD",
        {"A1": {"id": "A1", "connectorType": "association"}},
    )
    assert overrides["A1"]["source"] == "OTHER"
    assert any("prohibited fields:A1" in x for x in failures)


def test_topology_load_plan_rejects_non_association_and_frozen_extend_override(tmp_path):
    mod = _load_topology_module("topov2_extend")
    plan = tmp_path / "bad_extend.yaml"
    plan.write_text(
        yaml.safe_dump(
            {
                "plans": {
                    "BAD": {
                        "routes": {"EXT-07-06": {"targetSide": "LEFT"}}
                    }
                }
            }
        ),
        encoding="utf-8",
    )
    _, failures = mod.load_plan(
        plan,
        "BAD",
        {"EXT-07-06": {"id": "EXT-07-06", "connectorType": "extend"}},
    )
    assert any("not an Association:EXT-07-06" in x for x in failures)
    assert any("frozen Extend override prohibited:EXT-07-06" in x for x in failures)


def test_candidate_selector_avoids_exact_contact_and_finds_joint_solution():
    from route_candidate_selector import build_conflicts, make_candidate, solve_candidates

    raw = {
        "R1": [
            {"routeId": "R1", "family": "bad", "tag": "r1_bad", "cost": 1, "points": [[0, 1], [4, 1]]},
            {"routeId": "R1", "family": "good", "tag": "r1_good", "cost": 2, "points": [[0, 0], [4, 0]]},
        ],
        "R2": [
            {"routeId": "R2", "family": "vertical", "tag": "r2", "cost": 1, "points": [[2, 0.5], [2, 2]]},
        ],
    }
    by_route = {rid: [make_candidate(x) for x in xs] for rid, xs in raw.items()}
    conflicts = build_conflicts(by_route)
    assert "r2" in conflicts["r1_bad"]
    assert "r2" not in conflicts["r1_good"]
    result = solve_candidates(by_route, conflicts=conflicts)
    assert result["status"] == "PASS"
    assert result["solutions"][0]["selection"]["R1"]["key"] == "r1_good"


def test_candidate_selector_reports_unsatisfied_route():
    from route_candidate_selector import make_candidate, solve_candidates

    by_route = {
        "R1": [make_candidate({"routeId": "R1", "tag": "r1", "points": [[0, 1], [4, 1]]})],
        "R2": [make_candidate({"routeId": "R2", "tag": "r2", "points": [[2, 0], [2, 2]]})],
    }
    result = solve_candidates(by_route)
    assert result["status"] == "FAIL"
    assert result["deadEnds"]
