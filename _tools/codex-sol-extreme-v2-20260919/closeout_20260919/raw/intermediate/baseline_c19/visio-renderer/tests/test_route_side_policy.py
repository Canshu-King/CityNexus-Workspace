from pathlib import Path
import yaml
def test_route_side_policy():
 r=yaml.safe_load((Path(__file__).resolve().parents[1]/'phase1-routing.yaml').read_text(encoding='utf8'))['routes']['P1_UC_Overview']; assert all((x['family']=='traveler' and x['sourceSide']=='RIGHT' and x['targetSide']=='LEFT') or (x['family']=='provider' and x['sourceSide']=='LEFT' and x['targetSide']=='RIGHT') or (x['family']=='extend' and x['sourceSide'] in {'LEFT','RIGHT','TOP','BOTTOM'} and x['targetSide'] in {'LEFT','RIGHT','TOP','BOTTOM'}) for x in r)
