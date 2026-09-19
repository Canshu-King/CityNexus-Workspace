import yaml, heapq, random, math
from pathlib import Path
R=Path(r'D:\moodle\CityNexus\visio-renderer'); ROOT=R.parent
sem=yaml.safe_load((ROOT/'visio-spec/pages/p1_uc_overview.yaml').read_text(encoding='utf-8')); cand=yaml.safe_load((R/'phase1-routing-rc6-candidate.yaml').read_text(encoding='utf-8')); nodes={s['id']:s for s in sem['shapes'] if s['id']!='BOUNDARY'}
def box(n):return(n['x']-n['width']/2,n['y']-n['height']/2,n['x']+n['width']/2,n['y']+n['height']/2)
def port(n,s,f):
 b=box(n);f=float(f);return {'LEFT':(b[0],b[1]+(b[3]-b[1])*f),'RIGHT':(b[2],b[1]+(b[3]-b[1])*f),'TOP':(b[0]+(b[2]-b[0])*f,b[1]),'BOTTOM':(b[0]+(b[2]-b[0])*f,b[3])}[s]
def segs(p):return zip(p,p[1:])
def ori(a,b):return'H' if abs(a[1]-b[1])<1e-7 else'V' if abs(a[0]-b[0])<1e-7 else'D'
def contact(a,b,c,d):
 oa,ob=ori(a,b),ori(c,d)
 if 'D'in(oa,ob):return False
 if oa==ob=='H':return abs(a[1]-c[1])<1e-7 and max(min(a[0],b[0]),min(c[0],d[0]))<=min(max(a[0],b[0]),max(c[0],d[0]))+1e-7
 if oa==ob=='V':return abs(a[0]-c[0])<1e-7 and max(min(a[1],b[1]),min(c[1],d[1]))<=min(max(a[1],b[1]),max(c[1],d[1]))+1e-7
 if oa=='V':return contact(c,d,a,b)
 x=c[0];y=a[1];return min(a[0],b[0])-1e-7<=x<=max(a[0],b[0])+1e-7 and min(c[1],d[1])-1e-7<=y<=max(c[1],d[1])+1e-7
def inside(a,b,n):
 x1,y1=a;x2,y2=b;l,t,r,bt=box(n)
 if abs(y1-y2)<1e-7:return t+1e-7<y1<bt-1e-7 and max(min(x1,x2),l)<min(max(x1,x2),r)-1e-7
 return l+1e-7<x1<r-1e-7 and max(min(y1,y2),t)<min(max(y1,y2),bt)-1e-7
SC=2
blocked=set()
for ix in range(34*SC):
 for iy in range(20*SC):
  p=(ix/SC,iy/SC)
  if any((n['x']-n['width']/2)<p[0]<(n['x']+n['width']/2) and (n['y']-n['height']/2)<p[1]<(n['y']+n['height']/2) for n in nodes.values()):blocked.add((ix,iy))
frozen={r['id']:r for r in cand['routes'] if r.get('planningStatus')=='FROZEN_FROM_C4E1'}; alltodo=[r for r in cand['routes'] if r['id'] not in frozen]
def simplify(p):
 q=[p[0]]
 for z in p[1:]:
  if z==q[-1]:continue
  if len(q)>=2 and ((q[-2][0]==q[-1][0]==z[0]) or(q[-2][1]==q[-1][1]==z[1])):q[-1]=z
  else:q.append(z)
 return q
def find(route,paths):
 s=port(nodes[route['source']],route['sourceSide'],route['sourcePortFraction']);t=port(nodes[route['target']],route['targetSide'],route['targetPortFraction']); st=(round(s[0]*SC),round(s[1]*SC));go=(round(t[0]*SC),round(t[1]*SC))
 q=[(0,st)];prev={};dist={st:0}
 while q:
  _,u=heapq.heappop(q)
  if u==go:
   out=[];z=u
   while z in prev:out.append((z[0]/SC,z[1]/SC));z=prev[z]
   out.append(s);out.reverse();out[-1]=t;return simplify(out)
  for dx,dy in((1,0),(-1,0),(0,1),(0,-1)):
   v=(u[0]+dx,u[1]+dy)
   if not(0<=v[0]<34*SC and 0<=v[1]<20*SC) or v in blocked:continue
   a=(u[0]/SC,u[1]/SC);b=(v[0]/SC,v[1]/SC)
   if u==st and not((route['sourceSide']=='RIGHT' and dx>0)or(route['sourceSide']=='LEFT' and dx<0)or(route['sourceSide']=='TOP' and dy<0)or(route['sourceSide']=='BOTTOM' and dy>0)):continue
   if v==go and not((route['targetSide']=='LEFT' and dx>0)or(route['targetSide']=='RIGHT' and dx<0)or(route['targetSide']=='TOP' and dy>0)or(route['targetSide']=='BOTTOM' and dy<0)):continue
   if any(inside(a,b,n) for n in nodes.values()):continue
   if any(contact(a,b,c,d) for p in paths.values() for c,d in segs(p)):continue
   nd=dist[u]+1
   if nd<dist.get(v,10**9):dist[v]=nd;prev[v]=u;heapq.heappush(q,(nd+abs(v[0]-go[0])+abs(v[1]-go[1]),v))
 return None
best=0;bestpaths=None
for trial in range(200):
 paths={k:[port(nodes[v['source']],v['sourceSide'],v['sourcePortFraction']),*map(tuple,v['waypoints']),port(nodes[v['target']],v['targetSide'],v['targetPortFraction'])] for k,v in frozen.items()}
 order=list(alltodo);random.seed(trial);random.shuffle(order);good=0
 for r in order:
  p=find(r,paths)
  if p:paths[r['id']]=p;good+=1
 if good>best:best=good;bestpaths=paths;print('best',best,'trial',trial,flush=True)
 if good==len(alltodo):
  out=yaml.safe_load((R/'phase1-routing-rc6-candidate.yaml').read_text(encoding='utf-8'))
  for r in out['routes']:
   if r['id'] in paths and r['id'] not in frozen:r['waypoints']=[[x,y] for x,y in paths[r['id']][1:-1]];r['planningStatus']='ROUTE_PLANNED_PENDING_EXTERNAL_FREEZE'
  Path(r'D:\moodle\candidate-contact-clean.yaml').write_text(yaml.safe_dump(out,sort_keys=False,allow_unicode=True),encoding='utf-8');print('SUCCESS');break
