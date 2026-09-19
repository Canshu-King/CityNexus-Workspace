from pathlib import Path


def _validator():
    root = Path(__file__).resolve().parents[1]
    return (root / "calibration" / "validate_c4_fallback.py").read_text(encoding="utf-8")


def test_c4f_direction_validator_uses_indexed_cells_src():
    src = _validator()

    assert "VIS_SECTION_CONNECTION = 7" in src
    assert "VIS_CNNCT_DIRX = 2" in src
    assert "VIS_CNNCT_DIRY = 3" in src
    assert "shape.CellsSRC(" in src
    assert "row_index = alias_index - 1" in src


def test_c4f_direction_validator_does_not_use_unreliable_dirx_alias():
    src = _validator()

    assert 'CellsU(f"Connections.DirX' not in src
    assert 'CellsU(f"Connections.DirY' not in src
    assert '"directionEvidence": direction_evidence' in src


def test_c4f_openxml_audit_uses_persisted_connection_rows():
    root = Path(__file__).resolve().parents[1]
    src = (root / "calibration" / "audit_c4_fallback_openxml.py").read_text(encoding="utf-8")

    assert 'zf.read("visio/pages/page1.xml")' in src
    assert 'row_index = alias_index - 1' in src
    assert '"DirX"' in src
    assert '"DirY"' in src
