from pathlib import Path
import yaml
def test_route_family_counts():
 r=yaml.safe_load((Path(__file__).resolve().parents[1]/'phase1-routing.yaml').read_text(encoding='utf8'))['routes']['P1_UC_Overview']; c={x:sum(i['family']==x for i in r) for x in ('traveler','provider','extend')}; assert c=={'traveler':9,'provider':9,'extend':3}
