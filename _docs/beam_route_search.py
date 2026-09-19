import yaml,heapq,random,math,time,sys
from pathlib import Path
R=Path(r'D:\moodle\CityNexus\visio-renderer'); ROOT=R.parent
sem=yaml.safe_load((ROOT/'visio-spec/pages/p1_uc_overview.yaml').read_text(encoding='utf-8')); cand=yaml.safe_load((R/'phase1-routing-rc6-candidate.yaml').read_text(encoding='utf-8'))
nodes={s['id']:s for s in sem['shapes'] if s['id']!='BOUNDARY'}; SC=20; W=round(float(sem['pageWidth'])*SC);H=round(float(sem['pageHeight'])*SC)
def box(n):return(n['x']-n['width']/2,n['y']-n['height']/2,n['x']+n['width']/2,n['y']+n['height']/2)
def port(n,side,f):
 l,t,r,b=box(n);f=float(f);return {'LEFT':(l,t+(b-t)*f),'RIGHT':(r,t+(b-t)*f),'TOP':(l+(r-l)*f,t),'BOTTOM':(l+(r-l)*f,b)}[side]
def enc(p):return(int(round(p[0]*SC)),int(round(p[1]*SC)))
def dec(p):return(p[0]/SC,p[1]/SC)
def seg_inside(a,b,n):
 l,t,r,bt=box(n)
 if abs(a[1]-b[1])<1e-9:return t+1e-9<a[1]<bt-1e-9 and max(min(a[0],b[0]),l)<min(max(a[0],b[0]),r)-1e-9
 return l+1e-9<a[0]<r-1e-9 and max(min(a[1],b[1]),t)<min(max(a[1],b[1]),bt)-1e-9
def tangent(r,u,v,start):
 dx=v[0]-u[0];dy=v[1]-u[1]
 if start:return (r['sourceSide']=='RIGHT' and dx>0)or(r['sourceSide']=='LEFT' and dx<0)or(r['sourceSide']=='TOP' and dy<0)or(r['sourceSide']=='BOTTOM' and dy>0)
 return (r['targetSide']=='LEFT' and dx>0)or(r['targetSide']=='RIGHT' and dx<0)or(r['targetSide']=='TOP' and dy>0)or(r['targetSide']=='BOTTOM' and dy<0)
def simplify(p):
 out=[p[0]]
 for x in p[1:-1]:
  if len(out)>1 and ((out[-2][0]==out[-1][0]==x[0])or(out[-2][1]==out[-1][1]==x[1])):out[-1]=x
  else:out.append(x)
 out.append(p[-1]);return out
def occupied(paths):
 occ=set()
 for p in paths.values():
  for a,b in zip(p,p[1:]):
   x1,y1=enc(a);x2,y2=enc(b);dx=(x2>x1)-(x2<x1);dy=(y2>y1)-(y2<y1);x,y=x1,y1
   while True:
    occ.add((x,y))
    if (x,y)==(x2,y2):break
    x+=dx;y+=dy
 return occ
blocked=set()
for x in range(W+1):
 for y in range(H+1):
  p=dec((x,y))
  if any((lambda b:b[0]+1e-9<p[0]<b[2]-1e-9 and b[1]+1e-9<p[1]<b[3]-1e-9)(box(n)) for n in nodes.values()):blocked.add((x,y))
frozen={r['id']:r for r in cand['routes'] if r.get('planningStatus')=='FROZEN_FROM_C4E1'}; assoc=[r for r in cand['routes'] if r['id'] not in frozen]
def frozen_paths():return {r['id']:[port(nodes[r['source']],r['sourceSide'],r['sourcePortFraction']),*map(tuple,r['waypoints']),port(nodes[r['target']],r['targetSide'],r['targetPortFraction'])] for r in frozen.values()}
def astar(r,paths,seed,limit=150000):
 s=port(nodes[r['source']],r['sourceSide'],r['sourcePortFraction']);t=port(nodes[r['target']],r['targetSide'],r['targetPortFraction']); st=enc(s);go=enc(t);occ=occupied(paths);occ.discard(st);occ.discard(go); rng=random.Random(seed)
 # randomized costs
 noise={}
 def ncost(v):
  if v not in noise:noise[v]=rng.random()*0.15
  return noise[v]
 q=[(0,st,None)]; g={(st,None):0}; prev={}; seen=0
 while q and seen<limit:
  _,u,ld=heapq.heappop(q); seen+=1
  if u==go:
   z=(u,ld); seq=[]
   while z in prev:
    z0,dir0=z;seq.append(dec(z0));z=prev[z]
   seq.append(s); seq.reverse(); return simplify(seq)
  for dx,dy in ((1,0),(-1,0),(0,1),(0,-1)):
   v=(u[0]+dx,u[1]+dy)
   if not(0<=v[0]<=W and 0<=v[1]<=H) or v in blocked:continue
   if u==st and not tangent(r,u,v,True):continue
   if v==go and not tangent(r,u,v,False):continue
   if v in occ and v not in (st,go):continue
   a,b=dec(u),dec(v)
   if any(seg_inside(a,b,n) for nid,n in nodes.items() if nid not in (r['source'],r['target'])):continue
   ndir=(dx,dy); bend=0.3 if ld is not None and ld!=ndir else 0
   key=(v,ndir); ng=g[(u,ld)]+1+bend+ncost(v)
   if ng<g.get(key,1e18):
    g[key]=ng;prev[key]=(u,ld);h=abs(v[0]-go[0])+abs(v[1]-go[1]);heapq.heappush(q,(ng+h,v,ndir))
 return None
def gen(r,paths,k=6):
 out=[];seen=set()
 for i in range(k):
  p=astar(r,paths,i*104729+len(paths)*31,250000)
  if p:
   key=tuple(p)
   if key not in seen:seen.add(key);out.append(p)
 return out
# route order heuristics: provider then traveler by target, but beam selects fixed order
order=sorted(assoc,key=lambda r:(0 if r['family']=='provider' else 1, abs(nodes[r['target']]['y']-nodes[r['source']]['y'])),reverse=True)
print('order',[r['id'] for r in order],flush=True)
beam=[(0,frozen_paths())]; start=time.time()
for depth,r in enumerate(order):
 nxt=[]
 for score,paths in beam:
  ps=gen(r,paths,8)
  for j,p in enumerate(ps):
   np=dict(paths);np[r['id']]=p
   # score length + bends
   nxt.append((score+len(p)+j*0.01,np))
 if not nxt:
  print('NO at',depth,r['id']);break
 nxt.sort(key=lambda x:x[0]); beam=nxt[:80]
 print('depth',depth+1,'route',r['id'],'states',len(nxt),'beam',len(beam),'elapsed',round(time.time()-start,1),flush=True)
# choose state with max depth and write top candidates
if beam:
 bestpaths=beam[0][1];out=yaml.safe_load((R/'phase1-routing-rc6-candidate.yaml').read_text(encoding='utf-8'))
 for rr in out['routes']:
  if rr['id'] in bestpaths and rr.get('planningStatus')!='FROZEN_FROM_C4E1':rr['waypoints']=[[float(x),float(y)] for x,y in bestpaths[rr['id']][1:-1]];rr['planningStatus']='ROUTE_PLANNED_PENDING_EXTERNAL_FREEZE'
 Path(r'D:\moodle\candidate-beam-best.yaml').write_text(yaml.safe_dump(out,sort_keys=False,allow_unicode=True),encoding='utf-8')
 print('wrote',len(bestpaths),flush=True)
