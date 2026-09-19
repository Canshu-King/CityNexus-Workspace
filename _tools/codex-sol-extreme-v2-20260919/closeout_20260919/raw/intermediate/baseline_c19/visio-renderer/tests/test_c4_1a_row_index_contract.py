from pathlib import Path


def test_builder_uses_real_visrowlast_and_cells_src():
    root = Path(__file__).resolve().parents[1]
    src = (root / 'calibration' / 'build_c4_1a.py').read_text(encoding='utf-8')
    assert 'VIS_ROW_LAST = -2' in src
    assert 'CellsSRC(VIS_SECTION_CONNECTION' in src
    assert 'CellsSRC(VIS_SECTION_GEOMETRY_1' in src
    assert 'VIS_TAG_CONNECTION_POINT = 153' in src
    assert 'VIS_TAG_LINE_TO = 139' in src


def test_builder_does_not_use_addrow_return_as_cellsu_suffix():
    root = Path(__file__).resolve().parents[1]
    src = (root / 'calibration' / 'build_c4_1a.py').read_text(encoding='utf-8')
    assert 'Connections.X{row}' not in src
    assert 'Geometry1.X{ix}' not in src
