"""Regression coverage for corridor loss during route normalization."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "calibration"))
from plan_p1_associations import compact, candidate_to_route, make_candidate


def test_compression_preserves_reversal_for_subsequent_rejection():
    assert compact([(0, 0), (2, 0), (1, 0)]) == [(0, 0), (2, 0), (1, 0)]
    assert compact([(0, 0), (1, 0), (2, 0)]) == [(0, 0), (2, 0)]


def test_candidate_conversion_retains_semantic_identity():
    route = dict(id="A", connectorType="association", source="S", target="T",
                 sourceSide="RIGHT", targetSide="LEFT", lane="original")
    candidate = make_candidate(dict(routeId="A", points=[[0, 0], [1, 0], [1, 1], [2, 1]]))
    result = candidate_to_route(route, candidate)
    assert all(result[k] == v for k, v in route.items())
    assert result["waypoints"] == [[1, 0], [1, 1]]
    assert "waypoints" not in route
