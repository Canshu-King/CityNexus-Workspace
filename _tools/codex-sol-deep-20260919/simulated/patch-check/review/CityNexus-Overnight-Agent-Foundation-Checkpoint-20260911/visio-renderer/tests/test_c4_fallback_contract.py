from pathlib import Path
import ast


def _root():
    return Path(__file__).resolve().parents[1]


def test_fallback_builder_never_mutates_native_geometry_section():
    src = (_root() / "calibration" / "build_c4_fallback.py").read_text(encoding="utf-8")
    tree = ast.parse(src)

    forbidden_calls = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
            continue
        if node.func.attr in {"DeleteRow"}:
            forbidden_calls.append(node.func.attr)

    assert forbidden_calls == []
    assert "VIS_SECTION_GEOMETRY_1" not in src


def test_fallback_preserves_native_semantic_association_and_hides_only_stroke():
    src = (_root() / "calibration" / "build_c4_fallback.py").read_text(encoding="utf-8")
    assert 'Masters.ItemU("Association")' in src
    assert 'conn.CellsU("BeginX").GlueTo' in src
    assert 'conn.CellsU("EndX").GlueTo' in src
    assert '"RoutingMechanic": "native-semantic-hidden-plus-presentation-segments"' in src
    assert 'force(shape.CellsU("LinePattern"), "0")' in src


def test_fallback_visible_route_is_drawline_segment_overlay():
    src = (_root() / "calibration" / "build_c4_fallback.py").read_text(encoding="utf-8")
    assert "page.DrawLine(" in src
    assert '"ContentRole", "route-segment"' in src
    assert '"OwnerSpecId", active_route' in src
    assert '"SegmentIndex", index' in src
    assert '"SegmentCount", segment_count' in src


def test_fallback_validator_keeps_semantics_and_geometry_gates():
    src = (_root() / "calibration" / "validate_c4_fallback.py").read_text(encoding="utf-8")
    for token in [
        "nativeAssociationRatio",
        "semanticFullyGluedRatio",
        "semanticExplicitSidePortRatio",
        "semanticDirectionalSidePortRatio",
        "semanticHiddenStrokeRatio",
        "presentationSegmentGeometryMatchRatio",
        "presentationExactRouteRatio",
        "presentationOrthogonalRouteRatio",
        "connectorConnectorCrossingCount",
        "connectorThroughUnrelatedNodeCount",
    ]:
        assert token in src
