from pathlib import Path


def _src():
    root = Path(__file__).resolve().parents[1]
    return (root / "calibration" / "build_c4_1c.py").read_text(encoding="utf-8")


def test_c41c_preserves_native_terminal_linetow():
    src = _src()
    assert "for row in range(row_count - 1, 2, -1)" in src
    assert "trimmed_count not in (2, 3)" in src
    assert "Geometry1 row 2 is not LineTo" in src
    assert "reuse-native-terminal-lineto" in src


def test_c41c_rewrites_moveto_and_terminal_linetow_before_appending():
    src = _src()
    assert "CellsSRC(VIS_SECTION_GEOMETRY_1, 1, VIS_X)" in src
    assert "CellsSRC(VIS_SECTION_GEOMETRY_1, 2, VIS_X)" in src
    assert "for local_x, local_y in local_points[next_point_index:]" in src
    assert "expected_count = len(local_points) + 1" in src


def test_c41c_failure_diagnostics_survive_normalizer_errors():
    src = _src()
    assert 'diagnostics["postTrimRowCount"]' in src
    assert 'diagnostics["postTrimRows"]' in src
    assert 'diagnostics["normalizationMode"]' in src
    assert "route_diagnostics[active_route]," in src


def test_c41c_validator_checks_exact_geometry_contract():
    root = Path(__file__).resolve().parents[1]
    src = (root / "calibration" / "validate_c4_1c.py").read_text(encoding="utf-8")
    assert "geometryRowTypesValid" in src
    assert "manualWaypointMatchRatio" in src
    assert "orthogonalRouteRatio" in src
