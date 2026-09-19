import yaml, heapq, random, math, json
from pathlib import Path
R=Path(r'D:\moodle\CityNexus\visio-renderer'); ROOT=R.parent
sem=yaml.safe_load((ROOT/'visio-spec/pages/p1_uc_overview.yaml').read_text(encoding='utf-8')); cand=yaml.safe_load((R/'phase1-routing-rc6-candidate.yaml').read_text(encoding='utf-8'))
nodes={s['id']:s for s in sem['shapes'] if s['id']!='BOUNDARY'}
SC=20; W=int(round(float(sem['pageWidth'])*SC)); H=int(round(float(sem['pageHeight'])*SC))
def box(n):return(n['x']-n['width']/2,n['y']-n['height']/2,n['x']+n['width']/2,n['y']+n['height']/2)
def port(n,side,f):
 l,t,r,b=box(n);f=float(f);return {'LEFT':(l,t+(b-t)*f),'RIGHT':(r,t+(b-t)*f),'TOP':(l+(r-l)*f,t),'BOTTOM':(l+(r-l)*f,b)}[side]
def enc(p):return(int(round(p[0]*SC)),int(round(p[1]*SC)))
def dec(p):return(p[0]/SC,p[1]/SC)
def inside_segment(a,b,n):
 l,t,r,bt=box(n); x1,y1=a;x2,y2=b
 if abs(y1-y2)<1e-9:return t+1e-9<y1<bt-1e-9 and max(min(x1,x2),l)<min(max(x1,x2),r)-1e-9
 if abs(x1-x2)<1e-9:return l+1e-9<x1<r-1e-9 and max(min(y1,y2),t)<min(max(y1,y2),bt)-1e-9
 return True
def tangent(route,u,v,start=True):
 dx=v[0]-u[0];dy=v[1]-u[1]
 if start:
  return (route['sourceSide']=='RIGHT' and dx>0) or (route['sourceSide']=='LEFT' and dx<0) or (route['sourceSide']=='TOP' and dy<0) or (route['sourceSide']=='BOTTOM' and dy>0)
 return (route['targetSide']=='LEFT' and dx>0) or (route['targetSide']=='RIGHT' and dx<0) or (route['targetSide']=='TOP' and dy>0) or (route['targetSide']=='BOTTOM' and dy<0)
def build_res(paths):
 occ=set()
 for p in paths.values():
  for a,b in zip(p,p[1:]):
   x1,y1=enc(a);x2,y2=enc(b);dx=0 if x1==x2 else (1 if x2>x1 else -1);dy=0 if y1==y2 else (1 if y2>y1 else -1)
   x,y=x1,y1; occ.add((x,y))
   while (x,y)!=(x2,y2): x+=dx;y+=dy;occ.add((x,y))
 return occ
# node blocked vertices strictly interior
blocked=set()
for x in range(W+1):
 for y in range(H+1):
  px,py=dec((x,y))
  if any((lambda b:b[0]+1e-9<px<b[2]-1e-9 and b[1]+1e-9<py<b[3]-1e-9)(box(n)) for n in nodes.values()):blocked.add((x,y))
# frozen routes
frozen={r['id']:r for r in cand['routes'] if r.get('planningStatus')=='FROZEN_FROM_C4E1'}
allassoc=[r for r in cand['routes'] if r['id'] not in frozen]
def initial_frozen():return {r['id']:[port(nodes[r['source']],r['sourceSide'],r['sourcePortFraction']),*map(tuple,r['waypoints']),port(nodes[r['target']],r['targetSide'],r['targetPortFraction'])] for r in frozen.values()}
def find(route, paths, timeout_nodes=500000):
 s=port(nodes[route['source']],route['sourceSide'],route['sourcePortFraction']); t=port(nodes[route['target']],route['targetSide'],route['targetPortFraction']); st=enc(s);go=enc(t); occ=build_res(paths); occ.discard(st); occ.discard(go)
 # keep target/source endpoint but all other route points occupied
 def valid(v):
  x,y=v
  if not(0<=x<=W and 0<=y<=H):return False
  if v in blocked and v not in (st,go):return False
  return True
 q=[(0,st)]; g={st:0}; prev={}; seen=0
 while q and seen<timeout_nodes:
  _,u=heapq.heappop(q);seen+=1
  if u==go:
   seq=[];z=u
   while z in prev:seq.append(dec(z));z=prev[z]
   seq.append(s);seq.reverse(); return simplify(seq)
  for dx,dy in ((1,0),(-1,0),(0,1),(0,-1)):
   v=(u[0]+dx,u[1]+dy)
   if not valid(v):continue
   if u==st and not tangent(route,u,v,True):continue
   if v==go and not tangent(route,u,v,False):continue
   # avoid occupied lattice points; allow own start/goal only
   if v in occ and v not in (go,st):continue
   # edge interior must avoid node interiors; one-cell edge enough
   a,b=dec(u),dec(v)
   if any(inside_segment(a,b,n) for nid,n in nodes.items() if nid not in (route['source'],route['target'])):continue
   ng=g[u]+1
   if ng<g.get(v,10**9):
    g[v]=ng;prev[v]=u
    # modest bend penalty based on prev direction
    heapq.heappush(q,(ng+abs(v[0]-go[0])+abs(v[1]-go[1]),v))
 return None
def simplify(p):
 if len(p)<3:return p
 out=[p[0]]
 for i in range(1,len(p)-1):
  a=out[-1];b=p[i];c=p[i+1]
  if (abs(a[0]-b[0])<1e-9 and abs(b[0]-c[0])<1e-9) or (abs(a[1]-b[1])<1e-9 and abs(b[1]-c[1])<1e-9):continue
  out.append(b)
 out.append(p[-1]); return out
# try many orders, prioritize terminals by y groups
best=0; bestpaths=None
for trial in range(300):
 paths=initial_frozen(); order=list(allassoc); random.Random(trial*991+7).shuffle(order)
 # choose hard first (long/central) occasionally
 if trial%3==0:
  order.sort(key=lambda r: abs(nodes[r['target']]['x']-nodes[r['source']]['x'])+0.2*abs(nodes[r['target']]['y']-nodes[r['source']]['y']),reverse=True)
 good=0
 for r in order:
  p=find(r,paths,timeout_nodes=250000)
  if p is not None: paths[r['id']]=p;good+=1
  else: break
 if good>best:
  best=good;bestpaths=paths;print('BEST',best,'trial',trial,flush=True)
 if good==len(allassoc):
  print('FOUND',trial); break
print('done',best,'of',len(allassoc))
if bestpaths:
 out=yaml.safe_load((R/'phase1-routing-rc6-candidate.yaml').read_text(encoding='utf-8'))
 for r in out['routes']:
  if r['id'] in bestpaths and r.get('planningStatus')!='FROZEN_FROM_C4E1':
   r['waypoints']=[[float(x),float(y)] for x,y in bestpaths[r['id']][1:-1]]
   r['planningStatus']='ROUTE_PLANNED_PENDING_EXTERNAL_FREEZE'
 Path(r'D:\moodle\candidate-grid-best.yaml').write_text(yaml.safe_dump(out,sort_keys=False,allow_unicode=True),encoding='utf-8')
