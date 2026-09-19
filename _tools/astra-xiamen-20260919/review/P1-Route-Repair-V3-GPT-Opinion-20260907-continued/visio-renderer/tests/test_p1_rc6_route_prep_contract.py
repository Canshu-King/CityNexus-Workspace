from pathlib import Path
import yaml
ROOT=Path(__file__).resolve().parents[1]
def test_candidate_covers_21():
    c=yaml.safe_load((ROOT/"phase1-routing-rc6-candidate.yaml").read_text(encoding="utf-8"))
    s=yaml.safe_load((ROOT.parent/"visio-spec"/"pages"/"p1_uc_overview.yaml").read_text(encoding="utf-8"))
    assert len(c["routes"])==21
    assert {x["id"] for x in c["routes"]}=={x["id"] for x in s["connectors"]}
def test_current_route_planning_contract():
    c=yaml.safe_load((ROOT/"phase1-routing-rc6-candidate.yaml").read_text(encoding="utf-8"))
    s=yaml.safe_load((ROOT.parent/"visio-spec"/"pages"/"p1_uc_overview.yaml").read_text(encoding="utf-8"))
    assert {x["id"] for x in c["routes"]}=={x["id"] for x in s["connectors"]}
    frozen={x["id"] for x in c["routes"] if x["planningStatus"]=="FROZEN_FROM_C4E1"}
    assert frozen=={"EXT-07-06","EXT-09-08","EXT-10-09"}
    associations=[x for x in c["routes"] if x["connectorType"]=="association"]
    assert len(associations)==18
    assert all(isinstance(x["waypoints"], list) and x["waypoints"] for x in associations)
    assert c["metadata"]["status"] in {"PLANNING_REQUIRED", "GEOMETRY_PASS_PENDING_EXTERNAL_FREEZE"}
def test_validator_enforces_geometry_quality():
    src=(ROOT/"calibration"/"validate_p1_route_candidate.py").read_text(encoding="utf-8")
    for token in ("tangent_ok","count_crossings","count_overlaps","through unrelated node","explicit waypoints not planned"):
        assert token in src
