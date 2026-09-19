from pathlib import Path
import ast
import yaml


ROOT = Path(__file__).resolve().parents[1]


def test_c4e_spec_has_exact_three_formal_extend_relations():
    spec = yaml.safe_load(
        (ROOT / "calibration" / "c4-extend-calibration-spec.yaml").read_text(encoding="utf-8")
    )
    routes = spec["routes"]
    assert [r["id"] for r in routes] == ["EXT-07-06", "EXT-09-08", "EXT-10-09"]
    assert all(r["connectorType"] == "extend" for r in routes)
    assert all(r["sourceSide"] == "TOP" and r["targetSide"] == "BOTTOM" for r in routes)
    assert [r["condition"] for r in routes] == [
        "[payment required]",
        "[event detected]",
        "[replan required]",
    ]


def test_c4e_builder_uses_native_extend_without_geometry_mutation():
    src = (ROOT / "calibration" / "build_c4_extend.py").read_text(encoding="utf-8")
    tree = ast.parse(src)

    assert 'Masters.ItemU("Extend")' in src
    assert 'conn.CellsU("BeginX").GlueTo' in src
    assert 'conn.CellsU("EndX").GlueTo' in src
    assert '"native-extend-hidden-plus-presentation-segments"' in src
    assert "VIS_SECTION_GEOMETRY_1" not in src

    delete_calls = [
        n for n in ast.walk(tree)
        if isinstance(n, ast.Call)
        and isinstance(n.func, ast.Attribute)
        and n.func.attr == "DeleteRow"
    ]
    assert delete_calls == []


def test_c4e_builder_uses_dashed_segments_terminal_arrow_and_text_shapes():
    src = (ROOT / "calibration" / "build_c4_extend.py").read_text(encoding="utf-8")
    assert "page.DrawLine(" in src
    assert 'force(shape.CellsU("LinePattern"), "2")' in src
    assert "native_open_arrow_code" in src
    assert 'content_role="extend-label"' in src
    assert 'content_role="extend-condition"' in src
    assert '"OwnerSpecId"' in src


def test_c4e_validator_has_full_semantic_and_presentation_gate():
    src = (ROOT / "calibration" / "validate_c4_extend.py").read_text(encoding="utf-8")
    required = [
        "nativeExtendRatio",
        "semanticFullyGluedRatio",
        "semanticExplicitSidePortRatio",
        "semanticDirectionalSidePortRatio",
        "semanticHiddenStrokeRatio",
        "presentationSegmentGeometryMatchRatio",
        "presentationSegmentStyleRatio",
        "presentationExactRouteRatio",
        "presentationOrthogonalRouteRatio",
        "terminalOpenArrowRatio",
        "extendLabelRatio",
        "extendConditionRatio",
        "connectorConnectorCrossingCount",
        "connectorThroughUnrelatedNodeCount",
    ]
    for token in required:
        assert token in src
