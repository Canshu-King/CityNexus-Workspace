#!/usr/bin/env python3
"""Topological pre-gate for CityNexus P1_UC_Overview route planning.

Why this exists:
A contact-free orthogonal drawing is impossible if the clockwise cyclic order
of connector ports induces a non-planar rotation system.  Waypoint A* cannot
repair a topological contradiction in port order.

This tool is pure Python and does not call Visio/COM.  It checks the connector
rotation system before geometry routing.  It may apply one named Association
port-plan override from P1_ROUTE_PORT_PLANS.yaml.
"""
from __future__ import annotations
import argparse, json, math
from collections import defaultdict, deque
from pathlib import Path
import yaml


def node_box(n):
    x=float(n['x']); y=float(n['y']); w=float(n['width']); h=float(n['height'])
    return x-w/2, y-h/2, x+w/2, y+h/2


def perimeter_cw(n, side, fraction):
    """Clockwise perimeter parameter in the project's top-left-origin space."""
    l,t,r,b=node_box(n); w=r-l; h=b-t; f=float(fraction)
    if side=='TOP': return f*w
    if side=='RIGHT': return w+f*h
    if side=='BOTTOM': return w+h+(1-f)*w
    if side=='LEFT': return 2*w+h+(1-f)*h
    raise ValueError(f'bad side {side}')


def load_override(path, plan_id):
    if not path: return {}
    doc=yaml.safe_load(Path(path).read_text(encoding='utf-8')) or {}
    plans=doc.get('plans',{})
    if plan_id not in plans:
        raise SystemExit(f'plan not found: {plan_id}; available={list(plans)}')
    return plans[plan_id].get('routes',{})


def connected(node_ids, edges):
    g=defaultdict(list)
    for _,u,v in edges:g[u].append(v);g[v].append(u)
    start=next(iter(node_ids));seen={start};q=deque([start])
    while q:
        u=q.popleft()
        for v in g[u]:
            if v not in seen:seen.add(v);q.append(v)
    return seen==set(node_ids)


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
    overrides=load_override(args.plans,args.plan) if args.plan else {}
    nodes={s['id']:s for s in sem['shapes'] if s['id']!='BOUNDARY'}
    edges=[];inc=defaultdict(list);ports={};route_between={}
    for base in cand['routes']:
        r=dict(base); r.update(overrides.get(r['id'],{}))
        rid=r['id'];u=r['source'];v=r['target'];edges.append((rid,u,v))
        inc[u].append((rid,v));inc[v].append((rid,u));route_between[(u,v)]=rid;route_between[(v,u)]=rid
        ports[(u,rid)]=(r['sourceSide'],float(r.get('sourcePortFraction',0.5)))
        ports[(v,rid)]=(r['targetSide'],float(r.get('targetPortFraction',0.5)))
    active={n for n,L in inc.items() if L}
    failures=[]
    if not connected(active,edges):failures.append('connector graph is disconnected; Euler genus formula here assumes connected graph')
    rotation={};detail={}
    for n,L in inc.items():
        arr=[]
        for rid,nb in L:
            side,frac=ports[(n,rid)];p=perimeter_cw(nodes[n],side,frac);arr.append((p,rid,nb,side,frac))
        arr.sort(key=lambda z:(z[0],z[1]))
        for a,b in zip(arr,arr[1:]):
            if abs(a[0]-b[0])<1e-9:
                failures.append(f'{n}: duplicate perimeter port position for {a[1]} and {b[1]}')
        rotation[n]=[nb for _,_,nb,_,_ in arr]
        detail[n]=[{'route':rid,'neighbor':nb,'side':side,'fraction':frac,'perimeterCW':p} for p,rid,nb,side,frac in arr]
    # Faces from dart permutation phi(u,v)=(v,next_cw_after_u_at_v).
    seen=set();faces=[]
    for rid,u,v in edges:
        for d in ((u,v),(v,u)):
            if d in seen:continue
            cur=d;face=[]
            while cur not in seen:
                seen.add(cur);a,b=cur;face.append(a)
                L=rotation[b];cur=(b,L[(L.index(a)+1)%len(L)])
            faces.append(face)
    V=len(active);E=len(edges);F=len(faces);genus=(2-V+E-F)/2.0
    if abs(genus-round(genus))>1e-9 or genus<0:failures.append(f'invalid orientable genus result: {genus}')
    if abs(genus)>1e-9:failures.append(f'non-planar port rotation system: genus={genus:g}; zero-contact routing is topologically impossible until port order changes')
    payload={
        'status':'PASS' if not failures else 'FAIL',
        'plan':args.plan or 'candidate-as-is',
        'vertices':V,'edges':E,'faces':F,'orientableGenus':genus,
        'rotationCW':rotation,'portDetail':detail,'facesCW':faces,'failures':failures,
    }
    text=json.dumps(payload,ensure_ascii=False,indent=2)
    print(text)
    if args.json_out:Path(args.json_out).write_text(text,encoding='utf-8')
    return 0 if payload['status']=='PASS' else 1
if __name__=='__main__':raise SystemExit(main())
