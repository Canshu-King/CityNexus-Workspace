#!/usr/bin/env python3
"""Hardened topology pre-gate for CityNexus P1 Association routing.

Differences from v1:
- validates that a port plan changes only allowed Association routing fields;
- protects the three C4E1 Extend routes from overrides;
- uses route-id darts instead of neighbour lookup, so face tracing is unambiguous;
- emits route-level rotations and edge/face incidence for use by a face-aware planner.

This is a PRE-GATE only. It does not replace V2/V3 geometry/contact validation.
"""
from __future__ import annotations
import argparse, json
from collections import defaultdict, deque
from pathlib import Path
import yaml

ALLOWED_OVERRIDE_KEYS = {"sourcePortFraction", "targetSide", "targetPortFraction"}
VALID_SIDES = {"LEFT", "RIGHT", "TOP", "BOTTOM"}
FROZEN_EXTEND_IDS = {"EXT-07-06", "EXT-09-08", "EXT-10-09"}


def node_box(n):
    x=float(n['x']); y=float(n['y']); w=float(n['width']); h=float(n['height'])
    return x-w/2, y-h/2, x+w/2, y+h/2


def perimeter_cw(n, side, fraction):
    l,t,r,b=node_box(n); w=r-l; h=b-t; f=float(fraction)
    if side=='TOP': return f*w
    if side=='RIGHT': return w+f*h
    if side=='BOTTOM': return w+h+(1-f)*w
    if side=='LEFT': return 2*w+h+(1-f)*h
    raise ValueError(f'bad side {side}')


def load_plan(path, plan_id, candidate_by_id):
    if not path or not plan_id:
        return {}, []
    doc=yaml.safe_load(Path(path).read_text(encoding='utf-8')) or {}
    plans=doc.get('plans',{})
    if plan_id not in plans:
        raise SystemExit(f'plan not found: {plan_id}; available={list(plans)}')
    overrides=plans[plan_id].get('routes',{}) or {}
    failures=[]
    for rid, ov in overrides.items():
        if rid not in candidate_by_id:
            failures.append(f'plan override references unknown route:{rid}')
            continue
        base=candidate_by_id[rid]
        if base.get('connectorType') != 'association':
            failures.append(f'plan override is not an Association:{rid}')
        bad=set(ov)-ALLOWED_OVERRIDE_KEYS
        if bad:
            failures.append(f'plan override changes prohibited fields:{rid}:{sorted(bad)}')
        if rid in FROZEN_EXTEND_IDS:
            failures.append(f'frozen Extend override prohibited:{rid}')
    return overrides, failures


def is_connected(vertices, edges):
    if not vertices: return True
    g=defaultdict(list)
    for rid,u,v in edges:
        g[u].append(v); g[v].append(u)
    start=next(iter(vertices)); seen={start}; q=deque([start])
    while q:
        u=q.popleft()
        for v in g[u]:
            if v not in seen: seen.add(v); q.append(v)
    return seen==set(vertices)


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--semantic',required=True)
    ap.add_argument('--candidate',required=True)
    ap.add_argument('--plans')
    ap.add_argument('--plan')
    ap.add_argument('--json-out')
    args=ap.parse_args()

    sem=yaml.safe_load(Path(args.semantic).read_text(encoding='utf-8'))
    cand=yaml.safe_load(Path(args.candidate).read_text(encoding='utf-8'))
    nodes={s['id']:s for s in sem['shapes'] if s['id']!='BOUNDARY'}
    candidate_by_id={r['id']:r for r in cand['routes']}
    overrides, failures=load_plan(args.plans,args.plan,candidate_by_id)

    edges=[]
    incidence=defaultdict(list)
    endpoint_port={}
    endpoint_neighbour={}

    for base in cand['routes']:
        r=dict(base)
        if r['id'] in overrides:
            r.update(overrides[r['id']])
        rid=r['id']; u=r['source']; v=r['target']
        if u not in nodes or v not in nodes:
            failures.append(f'route references missing node:{rid}:{u}->{v}')
            continue
        for side_key in ('sourceSide','targetSide'):
            if r.get(side_key) not in VALID_SIDES:
                failures.append(f'invalid side:{rid}:{side_key}={r.get(side_key)!r}')
        for frac_key in ('sourcePortFraction','targetPortFraction'):
            try: f=float(r.get(frac_key))
            except Exception:
                failures.append(f'invalid fraction:{rid}:{frac_key}={r.get(frac_key)!r}'); f=-1
            if not 0.0 < f < 1.0:
                failures.append(f'fraction outside (0,1):{rid}:{frac_key}={f}')
        edges.append((rid,u,v))
        # dart endpoint 0=source, 1=target
        incidence[u].append((rid,0)); incidence[v].append((rid,1))
        endpoint_neighbour[(rid,0)]=v; endpoint_neighbour[(rid,1)]=u
        endpoint_port[(rid,0)]=(r['sourceSide'],float(r['sourcePortFraction']))
        endpoint_port[(rid,1)]=(r['targetSide'],float(r['targetPortFraction']))

    active=set(incidence)
    if not is_connected(active,edges):
        failures.append('connector graph is disconnected; this gate expects one connected embedding')

    # sigma = next clockwise dart at the same vertex.
    sigma={}
    rotation_routes={}
    rotation_neighbours={}
    port_detail={}
    for node_id,darts in incidence.items():
        arr=[]
        for dart in darts:
            rid,end=dart; side,frac=endpoint_port[dart]
            p=perimeter_cw(nodes[node_id],side,frac)
            arr.append((p,rid,end,endpoint_neighbour[dart],side,frac))
        arr.sort(key=lambda x:(x[0],x[1],x[2]))
        for a,b in zip(arr,arr[1:]):
            if abs(a[0]-b[0])<1e-9:
                failures.append(f'{node_id}: duplicate perimeter port position for {a[1]} and {b[1]}')
        rot=[(rid,end) for _,rid,end,_,_,_ in arr]
        for i,d in enumerate(rot): sigma[d]=rot[(i+1)%len(rot)]
        rotation_routes[node_id]=[rid for _,rid,_,_,_,_ in arr]
        rotation_neighbours[node_id]=[nb for _,_,_,nb,_,_ in arr]
        port_detail[node_id]=[
            {'route':rid,'endpoint':end,'neighbor':nb,'side':side,'fraction':frac,'perimeterCW':p}
            for p,rid,end,nb,side,frac in arr
        ]

    # alpha flips each dart across its edge. face permutation phi = sigma o alpha.
    alpha={}
    for rid,u,v in edges:
        alpha[(rid,0)]=(rid,1); alpha[(rid,1)]=(rid,0)
    phi={d:sigma[alpha[d]] for d in alpha if alpha[d] in sigma}

    seen=set(); faces=[]; dart_face={}
    for d in phi:
        if d in seen: continue
        face_id=len(faces); cur=d; seq=[]
        while cur not in seen:
            seen.add(cur); dart_face[cur]=face_id
            rid,end=cur
            # departing vertex for this dart
            base=candidate_by_id[rid]
            vertex=base['source'] if end==0 else base['target']
            seq.append({'route':rid,'endpoint':end,'vertex':vertex})
            cur=phi[cur]
        faces.append(seq)

    V=len(active); E=len(edges); F=len(faces)
    genus=(2-V+E-F)/2.0
    if abs(genus-round(genus))>1e-9 or genus<0:
        failures.append(f'invalid orientable genus result:{genus}')
    if abs(genus)>1e-9:
        failures.append(f'non-planar port rotation system: genus={genus:g}')

    edge_faces={}
    for rid,_,_ in edges:
        edge_faces[rid]=[dart_face.get((rid,0)),dart_face.get((rid,1))]

    payload={
        'status':'PASS' if not failures else 'FAIL',
        'plan':args.plan or 'candidate-as-is',
        'vertices':V,'edges':E,'faces':F,'faceCount':F,'orientableGenus':genus,
        'rotationRoutesCW':rotation_routes,
        'rotationNeighboursCW':rotation_neighbours,
        'portDetail':port_detail,
        'faceCycles':faces,
        'edgeFaceIncidence':edge_faces,
        'allowedOverrideKeys':sorted(ALLOWED_OVERRIDE_KEYS),
        'frozenExtendIds':sorted(FROZEN_EXTEND_IDS),
        'failures':failures,
    }
    text=json.dumps(payload,ensure_ascii=False,indent=2)
    print(text)
    if args.json_out: Path(args.json_out).write_text(text,encoding='utf-8')
    return 0 if payload['status']=='PASS' else 1

if __name__=='__main__': raise SystemExit(main())
