from __future__ import annotations
import json, sys
from pathlib import Path
import yaml

HERE = Path(__file__).resolve().parent
RENDERER = HERE.parent
ROOT = RENDERER.parent
sys.path.insert(0, str(RENDERER))

from routing_geometry import Box, count_crossings, count_overlaps, path_is_orthogonal, route_points, segment_intersects_box_interior

SEMANTIC = ROOT/"visio-spec"/"pages"/"p1_uc_overview.yaml"
CANDIDATE = RENDERER/"phase1-routing-rc6-candidate.yaml"
REPORT = HERE/"out"/"P1_UC_ROUTE_CANDIDATE-report.json"

def outward(side):
    return {"LEFT":(-1,0),"RIGHT":(1,0),"TOP":(0,-1),"BOTTOM":(0,1)}[side]

def seg_dir(a,b,eps=1e-9):
    dx=float(b[0])-float(a[0]); dy=float(b[1])-float(a[1])
    if abs(dx)<=eps and abs(dy)<=eps: return (0,0)
    if abs(dx)>eps and abs(dy)>eps: return None
    if abs(dx)>eps: return (1 if dx>0 else -1,0)
    return (0,1 if dy>0 else -1)

def tangent_ok(points, source_side, target_side):
    if len(points)<2: return False
    s = seg_dir(points[0],points[1])
    t = seg_dir(points[-2],points[-1])
    so = outward(source_side); to = outward(target_side)
    return s==so and t==(-to[0],-to[1])

def main():
    sem=yaml.safe_load(SEMANTIC.read_text(encoding="utf-8"))
    cand=yaml.safe_load(CANDIDATE.read_text(encoding="utf-8"))
    shapes={s["id"]:s for s in sem["shapes"] if s["id"]!="BOUNDARY"}
    conns={c["id"]:c for c in sem["connectors"]}
    routes={x["id"]:x for x in cand["routes"]}
    failures=[]; records=[]; paths={}

    if set(routes)!=set(conns):
        failures.append(f"coverage mismatch missing={sorted(set(conns)-set(routes))} extra={sorted(set(routes)-set(conns))}")

    for rid in sorted(set(routes)&set(conns)):
        r=routes[rid]; c=conns[rid]; local=[]
        if r.get("source")!=c["source"] or r.get("target")!=c["target"]: local.append("source/target mismatch")
        if r.get("connectorType")!=c["type"]: local.append("connectorType mismatch")
        for k in ("sourcePortFraction","targetPortFraction"):
            v=r.get(k)
            if not isinstance(v,(int,float)) or not 0<float(v)<1: local.append("invalid "+k)

        w=r.get("waypoints")
        points=[]
        if not isinstance(w,list) or not w:
            local.append("explicit waypoints not planned")
        else:
            try: points=route_points(r,shapes)
            except Exception as exc: local.append("route_points failed:"+repr(exc))

        if points:
            if not path_is_orthogonal(points): local.append("non-orthogonal")
            if not tangent_ok(points,r["sourceSide"],r["targetSide"]): local.append("endpoint tangent mismatch")
            if any(x<0 or y<0 or x>float(sem["pageWidth"]) or y>float(sem["pageHeight"]) for x,y in points):
                local.append("out of page")
            for nid,node in shapes.items():
                if nid in (r["source"],r["target"]): continue
                b=Box(node["x"]-node["width"]/2,node["y"]-node["height"]/2,node["x"]+node["width"]/2,node["y"]+node["height"]/2)
                if any(segment_intersects_box_interior(a,bp,b) for a,bp in zip(points,points[1:])):
                    local.append("through unrelated node:"+nid); break
            paths[rid]=points

        failures.extend(f"{rid}:{x}" for x in local)
        records.append({"id":rid,"planningStatus":r.get("planningStatus"),"pointCount":len(points),"failures":local})

    crossings=count_crossings(paths) if paths else []
    overlaps=count_overlaps(paths) if paths else []
    if len(crossings)>int(cand["policy"]["maxCrossingsPerPage"]):
        failures.append(f"crossings {len(crossings)} > {cand['policy']['maxCrossingsPerPage']}")
    if len(overlaps)>int(cand["policy"]["maxOverlapsPerPage"]):
        failures.append(f"overlaps {len(overlaps)} > {cand['policy']['maxOverlapsPerPage']}")
    if len(paths)!=len(conns): failures.append(f"only {len(paths)}/{len(conns)} routes have explicit geometry")

    payload={
        "pageName":cand["pageName"],"status":"PASS" if not failures else "FAIL",
        "semanticConnectorCount":len(conns),"candidateRouteCount":len(routes),
        "explicitGeometryRouteCount":len(paths),"crossingCount":len(crossings),"crossingPairs":crossings,
        "overlapCount":len(overlaps),"overlapPairs":overlaps,"routes":records,"failures":failures,
    }
    REPORT.write_text(json.dumps(payload,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps(payload,ensure_ascii=True,indent=2))
    return 0 if not failures else 1

if __name__=="__main__":
    raise SystemExit(main())
