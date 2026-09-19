"""Prepare a reference plan without modifying the authoritative candidate."""
import argparse
import json
from pathlib import Path
import sys
import yaml
import networkx as nx

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
sys.path.insert(0, str(HERE.parent))
from routing_geometry import route_points, path_is_orthogonal, node_box, segment_intersects_box_interior
from audit_p1_route_contacts import classify_contact, collinear_redundant
from validate_p1_route_candidate import tangent_ok

sem = yaml.safe_load((ROOT / 'visio-spec/pages/p1_uc_overview.yaml').read_text(encoding='utf-8'))
cand = yaml.safe_load((HERE.parent / 'phase1-routing-rc6-candidate.yaml').read_text(encoding='utf-8'))
def resolve_skeleton(cli_path=None):
    candidates = []
    if cli_path:
        candidates.append(Path(cli_path).expanduser().resolve())
    candidates.extend([
        ROOT / 'traveler-corridor-skeleton.yaml',
        HERE / 'traveler-corridor-skeleton.yaml',
        ROOT.parent / 'handoff_20260907' / 'traveler-corridor-skeleton.yaml',
    ])
    for path in candidates:
        if path.is_file():
            return path
    rendered = '\n'.join(f'  - {p}' for p in candidates)
    raise FileNotFoundError('traveler-corridor-skeleton.yaml not found. Checked:\n' + rendered)

parser = argparse.ArgumentParser(description='Prepare P1 corridor reference without modifying the authoritative candidate.')
parser.add_argument('--skeleton', help='Optional explicit path to traveler-corridor-skeleton.yaml')
args = parser.parse_args()
SKELETON = resolve_skeleton(args.skeleton)
sk = yaml.safe_load(SKELETON.read_text(encoding='utf-8'))
nodes = {n['id']: n for n in sem['shapes'] if n['id'] != 'BOUNDARY'}
for r in sk['routes']:
    for end, point in [('source', r['waypoints'][0]), ('target', r['waypoints'][-1])]:
        b = node_box(nodes[r[end]])
        side = r[end + 'Side']
        r[end + 'PortFraction'] = ((point[1] - b.top) / (b.bottom - b.top) if side in ('LEFT', 'RIGHT') else (point[0] - b.left) / (b.right - b.left))
routes = sk['routes'] + [r for r in cand['routes'] if r['connectorType'] == 'extend']
paths = {r['id']: route_points(r, nodes) for r in routes}
failures = []
for r in routes:
    p = paths[r['id']]
    if not path_is_orthogonal(p) or not tangent_ok(p, r['sourceSide'], r['targetSide']):
        failures.append([r['id'], 'orthogonality/tangency'])
        continue
    for a, b in zip(p, p[1:]):
        if abs(a[0]-b[0])+abs(a[1]-b[1]) < .1-1e-8:
            failures.append([r['id'], 'short segment'])
        for nid, n in nodes.items():
            if nid not in (r['source'], r['target']) and segment_intersects_box_interior(a,b,node_box(n)):
                failures.append([r['id'], 'node', nid])
    if any(collinear_redundant(*p[i:i+3]) for i in range(len(p)-2)):
        failures.append([r['id'], 'redundancy'])
contacts = []
for i, ra in enumerate(routes):
    for rb in routes[i+1:]:
        if any(classify_contact(a,b,c,d) for a,b in zip(paths[ra['id']],paths[ra['id']][1:]) for c,d in zip(paths[rb['id']],paths[rb['id']][1:])):
            contacts.append([ra['id'],rb['id']])
g = nx.Graph((c['source'],c['target']) for c in sem['connectors'])
plan = []
for r in cand['routes']:
    if r['connectorType'] != 'association':
        continue
    ref = next((x for x in sk['routes'] if x['id']==r['id']),r)
    batch = 'A'
    if r['id'] in ('A-CD-UC-10','A-M-UC-10','A-T-UC-10','A-T-UC-11'): batch='B'
    elif r['id'] in ('A-B-06','A-PA-07'): batch='C'
    elif r['id'] in ('A-M-UC-08','A-CE-09','A-M-UC-04'): batch='D'
    elif r['id'] in ('A-CD-UC-04','A-CD-UC-05'): batch='E'
    plan.append(dict(id=r['id'],batch=batch,sourceSide=ref['sourceSide'],sourcePortFraction=ref['sourcePortFraction'],targetSide=ref['targetSide'],targetPortFraction=ref['targetPortFraction'],referenceWaypoints=ref['waypoints'],status='PROVISIONAL_NOT_GLOBALLY_VALIDATED'))
out = HERE / 'out'
out.mkdir(exist_ok=True)
(out/'P1-CORRIDOR-PREPLAN.json').write_text(json.dumps(plan,indent=2),encoding='utf-8')
(out/'P1-TRAVELER-EXACT-REFERENCE.yaml').write_text(yaml.safe_dump(sk,sort_keys=False),encoding='utf-8')
report = dict(skeletonPath=str(SKELETON),abstractGraphPlanar=nx.check_planarity(g)[0],subgraphRouteCount=len(routes),failures=failures,contactPairs=contacts,globalGeometrySolved=False)
(out/'P1-PREPLAN-VALIDATION.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps(report,indent=2))
