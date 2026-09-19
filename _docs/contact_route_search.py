import yaml, heapq, math, random
from pathlib import Path
R=Path(r'D:\moodle\CityNexus\visio-renderer'); ROOT=R.parent
sem=yaml.safe_load((ROOT/'visio-spec/pages/p1_uc_overview.yaml').read_text(encoding='utf-8')); cand=yaml.safe_load((R/'phase1-routing-rc6-candidate.yaml').read_text(encoding='utf-8')); nodes={s['id']:s for s in sem['shapes'] if s['id']!='BOUNDARY'}
def box(n): return (n['x']-n['width']/2,n['y']-n['height']/2,n['x']+n['width']/2,n['y']+n['height']/2)
def port(n,side,f):
 b=box(n); f=float(f)
 return {'LEFT':(b[0],b[1]+(b[3]-b[1])*f),'RIGHT':(b[2],b[1]+(b[3]-b[1])*f),'TOP':(b[0]+(b[2]-b[0])*f,b[1]),'BOTTOM':(b[0]+(b[2]-b[0])*f,b[3])}[side]
def orient(a,b): return 'H' if abs(a[1]-b[1])<1e-8 else 'V' if abs(a[0]-b[0])<1e-8 else 'D'
def contact(a,b,c,d):
 oa,ob=orient(a,b),orient(c,d)
 if 'D' in (oa,ob): return False
 if oa==ob=='H':
  if abs(a[1]-c[1])>1e-8:return False
  return max(min(a[0],b[0]),min(c[0],d[0])) <= min(max(a[0],b[0]),max(c[0],d[0]))+1e-8
 if oa==ob=='V':
  if abs(a[0]-c[0])>1e-8:return False
  return max(min(a[1],b[1]),min(c[1],d[1])) <= min(max(a[1],b[1]),max(c[1],d[1]))+1e-8
 if oa=='V': return contact(c,d,a,b)
 x=c[0]; y=a[1]
 return min(a[0],b[0])-1e-8<=x<=max(a[0],b[0])+1e-8 and min(c[1],d[1])-1e-8<=y<=max(c[1],d[1])+1e-8
def segs(p): return list(zip(p,p[1:]))
def inside(a,b,n):
 x1,y1=a;x2,y2=b; l,t,r,bt=box(n)
 if abs(y1-y2)<1e-8:
  return t+1e-8<y1<bt-1e-8 and max(min(x1,x2),l)<min(max(x1,x2),r)-1e-8
 x=x1; return l+1e-8<x<r-1e-8 and max(min(y1,y2),t)<min(max(y1,y2),bt)-1e-8
def point_inside(p,n):
 l,t,r,bt=box(n); return l+1e-8<p[0]<r-1e-8 and t+1e-8<p[1]<bt-1e-8
def tangent_ok(p,route):
 if len(p)<2:return False
 dx=p[1][0]-p[0][0];dy=p[1][1]-p[0][1]; ex=p[-1][0]-p[-2][0];ey=p[-1][1]-p[-2][1]
 return ((route['sourceSide']=='RIGHT' and dx>0) or (route['sourceSide']=='LEFT' and dx<0) or (route['sourceSide']=='TOP' and dy<0) or (route['sourceSide']=='BOTTOM' and dy>0)) and ((route['targetSide']=='LEFT' and ex>0) or (route['targetSide']=='RIGHT' and ex<0) or (route['targetSide']=='TOP' and ey>0) or (route['targetSide']=='BOTTOM' and ey<0))
frozen={r['id']:r for r in cand['routes'] if r.get('planningStatus')=='FROZEN_FROM_C4E1'}
paths={}
for r in cand['routes']:
 if r.get('planningStatus')=='FROZEN_FROM_C4E1': paths[r['id']]=[port(nodes[r['source']],r['sourceSide'],r['sourcePortFraction']),*map(tuple,r['waypoints']),port(nodes[r['target']],r['targetSide'],r['targetPortFraction'])]
def astar(route):
 s=port(nodes[route['source']],route['sourceSide'],route['sourcePortFraction']); t=port(nodes[route['target']],route['targetSide'],route['targetPortFraction']); sc=2
 def enc(p):return(round(p[0]*sc),round(p[1]*sc))
 def dec(p):return(p[0]/sc,p[1]/sc)
 st,go=enc(s),enc(t); blocked=set()
 for x in range(340):
  for y in range(191):
   p=dec((x,y))
   if any(nid not in (route['source'],route['target']) and point_inside(p,n) for nid,n in nodes.items()):blocked.add((x,y))
 q=[(0,st)];g={st:0};prev={}
 while q:
  _,u=heapq.heappop(q)
  if u==go:
   out=[];z=u
   while z in prev:out.append(dec(z));z=prev[z]
   out.append(dec(st));out.reverse();return out
  for dx,dy in ((1,0),(-1,0),(0,1),(0,-1)):
   v=(u[0]+dx,u[1]+dy)
   if not(0<=v[0]<=339 and 0<=v[1]<=190) or v in blocked:continue
   a,b=dec(u),dec(v)
   if u==st:
    if route['sourceSide']=='RIGHT' and dx<=0:continue
    if route['sourceSide']=='LEFT' and dx>=0:continue
    if route['sourceSide']=='TOP' and dy>=0:continue
    if route['sourceSide']=='BOTTOM' and dy<=0:continue
   if v==go:
    if route['targetSide']=='LEFT' and dx<=0:continue
    if route['targetSide']=='RIGHT' and dx>=0:continue
    if route['targetSide']=='TOP' and dy>=0:continue
    if route['targetSide']=='BOTTOM' and dy<=0:continue
   if any(inside(a,b,n) for nid,n in nodes.items() if nid not in (route['source'],route['target'])):continue
   if any(contact(a,b,c,d) for p in paths.values() for c,d in segs(p)):continue
   ng=g[u]+1
   if ng<g.get(v,10**9):
    g[v]=ng;prev[v]=u;heapq.heappush(q,(ng+abs(v[0]-go[0])+abs(v[1]-go[1]),v))
 return None
def simplify(p):
 out=[p[0]]
 for a,b in zip(p[1:-1],p[2:]):
  if (out[-1][0]==a[0]==b[0]) or (out[-1][1]==a[1]==b[1]):continue
  out.append(a)
 out.append(p[-1]);return out
alltodo=[r for r in cand['routes'] if r.get('planningStatus')!='FROZEN_FROM_C4E1']
bestpaths=None
for trial in range(30):
 todo=list(alltodo);random.seed(trial+12);random.shuffle(todo); paths={k:[port(nodes[v['source']],v['sourceSide'],v['sourcePortFraction']),*map(tuple,v['waypoints']),port(nodes[v['target']],v['targetSide'],v['targetPortFraction'])] for k,v in frozen.items()}
 good=0
 for r in todo:
  p=astar(r)
  if not p: continue
  p=simplify(p);paths[r['id']]=p;good+=1
 if bestpaths is None or good>(len(bestpaths)-len(frozen)): bestpaths=dict(paths);print('TRIAL',trial,'good',good)
 if good==len(alltodo):break
paths=bestpaths
print('paths',len(paths))
for r in cand['routes']:
 if r['id'] in paths and r.get('planningStatus')!='FROZEN_FROM_C4E1':
  r['waypoints']=[[float(x),float(y)] for x,y in paths[r['id']][1:-1]]
  r['planningStatus']='ROUTE_PLANNED_PENDING_EXTERNAL_FREEZE'
(Path(r'D:\moodle\candidate-contact-clean.yaml')).write_text(yaml.safe_dump(cand,sort_keys=False,allow_unicode=True),encoding='utf-8')
