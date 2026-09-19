from pathlib import Path
import yaml
def test_route_schema():
    root=Path(__file__).resolve().parents[2]; routes=yaml.safe_load((root/'visio-renderer'/'phase1-routing.yaml').read_text(encoding='utf8'))['routes']['P1_UC_Overview']
    assert len(routes)==21 and len({r['id'] for r in routes})==21
    assert all(r['sourceSide'] in {'LEFT','RIGHT','TOP','BOTTOM'} and r['targetSide'] in {'LEFT','RIGHT','TOP','BOTTOM'} and r['lane'] for r in routes)
