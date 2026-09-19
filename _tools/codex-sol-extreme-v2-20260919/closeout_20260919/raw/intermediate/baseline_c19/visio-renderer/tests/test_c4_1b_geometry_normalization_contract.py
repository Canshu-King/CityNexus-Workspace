from pathlib import Path


def test_c41b_normalizes_router_geometry_without_deleting_moveto():
    root = Path(__file__).resolve().parents[1]
    src = (root / "calibration" / "build_c4_1b.py").read_text(encoding="utf-8")

    assert "VIS_ROW_LAST = -2" in src
    assert "VIS_TAG_MOVE_TO = 138" in src
    assert "VIS_TAG_LINE_TO = 139" in src
    assert "connector.DeleteRow(VIS_SECTION_GEOMETRY_1, row)" in src
    assert "range(row_count - 1, 1, -1)" in src
    assert "Geometry1 row 1 is not MoveTo" in src

    # C4.1a's false assumption must not survive.
    assert "unexpected pre-existing Geometry1 rows before manual realization" not in src
    assert "if row_count > 3" not in src


def test_c41b_rebuilds_line_rows_after_preserved_moveto():
    root = Path(__file__).resolve().parents[1]
    src = (root / "calibration" / "build_c4_1b.py").read_text(encoding="utf-8")

    assert "post_delete_count != 2" in src
    assert "for local_x, local_y in local_points[1:]" in src
    assert "connector.AddRow(" in src
    assert "VIS_TAG_LINE_TO" in src
    assert "finalGeometryRows" in src


def test_c41b_validator_reads_geometry_by_cells_src_and_checks_row_types():
    root = Path(__file__).resolve().parents[1]
    src = (root / "calibration" / "validate_c4_1b.py").read_text(encoding="utf-8")

    assert "conn.RowCount(VIS_SECTION_GEOMETRY_1)" in src
    assert "conn.CellsSRC(VIS_SECTION_GEOMETRY_1, row, VIS_X)" in src
    assert "geometryRowTypesValid" in src
    assert "VIS_TAG_MOVE_TO" in src
    assert "VIS_TAG_LINE_TO" in src
