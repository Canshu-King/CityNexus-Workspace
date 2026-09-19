from pathlib import Path
import ast


def _builder():
    root = Path(__file__).resolve().parents[1]
    return (root / "calibration" / "build_c4_1d.py").read_text(encoding="utf-8")


def test_c41d_does_not_delete_geometry_rows():
    """Assert that executable code contains no .DeleteRow(...) call."""
    src = _builder()
    tree = ast.parse(src)
    delete_calls = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "DeleteRow"
    ]
    assert delete_calls == []
    assert "no-delete-expand-then-rewrite" in src


def test_c41d_expands_before_rewriting():
    src = _builder()
    append_pos = src.index("while int(connector.RowCount")
    rewrite_pos = src.index("for row, (local_x, local_y) in enumerate")
    assert append_pos < rewrite_pos
    assert "VIS_ROW_LAST" in src
    assert "VIS_TAG_LINE_TO" in src


def test_c41d_keeps_final_endpoint_during_expansion():
    src = _builder()
    assert "final_x, final_y = local_points[-1]" in src
    assert 'f"{final_x} in"' in src
    assert 'f"{final_y} in"' in src


def test_c41d_detects_runtime_reroute_during_value_writes():
    src = _builder()
    assert "Geometry1 structure changed during value rewrite" in src
    assert "rewriteSteps" in src
    assert "rowsAfterRewrite" in src


def test_c41d_validator_keeps_exact_waypoint_gate():
    root = Path(__file__).resolve().parents[1]
    src = (root / "calibration" / "validate_c4_1d.py").read_text(encoding="utf-8")
    assert "manualWaypointMatchRatio" in src
    assert "orthogonalRouteRatio" in src
    assert "geometryRowTypesValid" in src
