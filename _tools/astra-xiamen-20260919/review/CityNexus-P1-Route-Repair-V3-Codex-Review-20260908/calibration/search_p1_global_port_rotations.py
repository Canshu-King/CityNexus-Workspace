"""Search planar port rotations and hard-route them as complete P1 candidates."""
from __future__ import annotations

import argparse
import copy
import json
import random
import sys
from collections import Counter, defaultdict

import yaml

HERE = __import__("pathlib").Path(__file__).resolve().parent
ROOT = HERE.parent.parent
sys.path[:0] = [str(ROOT / "visio-renderer"), str(HERE)]

from routing_geometry import route_points
from route_p1_negotiated_grid import OUT, STAGING, astar, build_axes, build_graph, compact, path_resources
from audit_p1_route_contacts import classify_contact, contact_key, collinear_redundant

CANDIDATE = ROOT / "visio-renderer" / "phase1-routing-rc6-candidate.yaml"
SEMANTIC = ROOT / "visio-spec" / "pages" / "p1_uc_overview.yaml"
FROZEN = {"EXT-07-06", "EXT-09-08", "EXT-10-09"}


def box(node):
    return (float(node["x"])-float(node["width"])/2, float(node["y"])-float(node["height"])/2,
            float(node["x"])+float(node["width"])/2, float(node["y"])+float(node["height"])/2)


def perimeter(node, side, fraction):
    l,t,r,b=box(node);w=r-l;h=b-t;f=float(fraction)
    return {"TOP":f*w,"RIGHT":w+f*h,"BOTTOM":w+h+(1-f)*w,"LEFT":2*w+h+(1-f)*h}[side]


def target_options(node):
    l,t,r,b=box(node);w=r-l;h=b-t;out=[]
    # The port's coordinate along a side is always a 0.10 lane, retaining
    # V3-normalizable waypoint approaches.
    for side in ("TOP","BOTTOM"):
        for k in range(1, int(round(w*10))): out.append((side, k/(w*10)))
    for side in ("LEFT","RIGHT"):
        lo=int(__import__("math").ceil((t+0.05)*10)); hi=int(__import__("math").floor((b-0.05)*10))
        for q in range(lo,hi+1): out.append((side, (q/10-t)/h))
    return out


def genus(routes,nodes):
    inc=defaultdict(list); ports={}
    for r in routes.values():
        for end,vertex,side,fraction in ((0,r["source"],r["sourceSide"],r["sourcePortFraction"]),(1,r["target"],r["targetSide"],r["targetPortFraction"])):
            inc[vertex].append((r["id"],end)); ports[r["id"],end]=(side,fraction)
    sigma={}
    for v,darts in inc.items():
        ordered=sorted(darts,key=lambda d:(perimeter(nodes[v],*ports[d]),d))
        if any(abs(perimeter(nodes[v],*ports[a])-perimeter(nodes[v],*ports[b]))<1e-8 for a,b in zip(ordered,ordered[1:])): return None
        for a,b in zip(ordered,ordered[1:]+ordered[:1]):sigma[a]=b
    alpha={(rid,0):(rid,1) for rid in routes};alpha.update({(rid,1):(rid,0) for rid in routes})
    seen=set();faces=0
    for dart in alpha:
        if dart in seen:continue
        faces+=1;cur=dart
        while cur not in seen:seen.add(cur);cur=sigma[alpha[cur]]
    return (2-len(inc)+len(routes)-faces)/2


def contacts(staged,nodes):
    paths={r["id"]:route_points(r,nodes) for r in staged["routes"]};ids=list(paths);found=[]
    for i,a in enumerate(ids):
        for b in ids[i+1:]:
            seen=set()
            for p,q in zip(paths[a],paths[a][1:]):
                for u,v in zip(paths[b],paths[b][1:]):
                    item=classify_contact(p,q,u,v)
                    if item and contact_key(item) not in seen:
                        seen.add(contact_key(item));found.append((a,b,item))
    return found


def main():
    ap=argparse.ArgumentParser();ap.add_argument("--attempts",type=int,default=30000);ap.add_argument("--trials",type=int,default=10);ap.add_argument("--seed",type=int,default=20260907);args=ap.parse_args()
    semantic=yaml.safe_load(SEMANTIC.read_text(encoding="utf-8"));nodes={n["id"]:n for n in semantic["shapes"] if n["id"]!="BOUNDARY"}
    original=yaml.safe_load(CANDIDATE.read_text(encoding="utf-8"));base={r["id"]:copy.deepcopy(r) for r in original["routes"]}
    assoc=[r["id"] for r in base.values() if r["connectorType"]=="association"]
    frozen={rid:route_points(base[rid],nodes) for rid in FROZEN};target_groups=defaultdict(list);source_groups=defaultdict(list)
    for rid in assoc:target_groups[base[rid]["target"]].append(rid);source_groups[base[rid]["source"]].append(rid)
    options={target:target_options(nodes[target]) for target in target_groups};rng=random.Random(args.seed);best={"routed":0}
    for attempt in range(args.attempts):
        routes=copy.deepcopy(base)
        for source,ids in source_groups.items():
            if source=="ACT-TRAVELER": fractions=[(i+1)/10 for i in range(9)]
            else: fractions=[(i+1)/(len(ids)+1) for i in range(len(ids))]
            rng.shuffle(fractions)
            for rid,f in zip(ids,fractions):routes[rid]["sourcePortFraction"]=f
        for target,ids in target_groups.items():
            rng.shuffle(ids);choices=options[target][:];rng.shuffle(choices);used=[]
            for rid in ids:
                for side,f in choices:
                    p=perimeter(nodes[target],side,f)
                    if all(abs(p-v)>1e-6 for v in used):
                        routes[rid]["targetSide"]=side;routes[rid]["targetPortFraction"]=f;used.append(p);break
        if genus(routes,nodes)!=0:continue
        mutable=[routes[rid] for rid in assoc];xs,ys=build_axes(semantic,mutable,nodes,frozen);ix,iy,allowed=build_graph(xs,ys,nodes,frozen)
        for trial in range(args.trials):
            order=assoc[:];rng.shuffle(order);vu=Counter();eu=Counter();paths={};failure=None
            for rid in order:
                path=astar(routes[rid],nodes,xs,ys,ix,iy,allowed,vu,eu,Counter(),Counter(),0.0,0.2,rng,hard=True,noise=0.005)
                if path is None:failure=rid;break
                paths[rid]=path;vs,es=path_resources(path,xs,ys);vu.update(vs);eu.update(es)
            if len(paths)>best["routed"]:
                best={"routed":len(paths),"attempt":attempt,"trial":trial,"failure":failure};print(json.dumps(best),flush=True)
            if len(paths)!=len(assoc):continue
            staged=copy.deepcopy(original);staged["metadata"]["status"]="STAGING_GEOMETRY_CANDIDATE"
            for route in staged["routes"]:
                rid=route["id"]
                if rid not in paths:continue
                for key in ("sourcePortFraction","targetSide","targetPortFraction"):route[key]=routes[rid][key]
                route["waypoints"]=[[round(x,2),round(y,2)] for x,y in compact(paths[rid])[1:-1]];route["planningStatus"]="ROUTE_PLANNED_PENDING_EXTERNAL_FREEZE"
            found=contacts(staged,nodes)
            if found:continue
            OUT.mkdir(parents=True,exist_ok=True);STAGING.write_text(yaml.safe_dump(staged,sort_keys=False),encoding="utf-8")
            result={"status":"PASS","attempt":attempt,"trial":trial,"stagingCandidate":str(STAGING),"best":best};print(json.dumps(result));return 0
    print(json.dumps({"status":"FAIL","best":best,"attempts":args.attempts}));return 2

if __name__=="__main__":raise SystemExit(main())
