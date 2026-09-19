import yaml, random, math
from pathlib import Path
R=Path(r'D:\moodle\CityNexus\visio-renderer'); ROOT=R.parent
sem=yaml.safe_load((ROOT/'visio-spec/pages/p1_uc_overview.yaml').read_text(encoding='utf-8')); cand=yaml.safe_load((R/'phase1-routing-rc6-candidate.yaml').read_text(encoding='utf-8')); nodes={s['id']:s for s in sem['shapes'] if s['id']!='BOUNDARY'}
def box(n):return(n['x']-n['width']/2,n['y']-n['height']/2,n['x']+n['width']/2,n['y']+n['height']/2)
def port(n,side,f):
 b=box(n);f=float(f);return {'LEFT':(b[0],b[1]+(b[3]-b[1])*f),'RIGHT':(b[2],b[1]+(b[3]-b[1])*f),'TOP':(b[0]+(b[2]-b[0])*f,b[1]),'BOTTOM':(b[0]+(b[2]-b[0])*f,b[3])}[side]
def segs(p):return list(zip(p,p[1:]))
def ori(a,b):return 'H' if abs(a[1]-b[1])<1e-7 else 'V' if abs(a[0]-b[0])<1e-7 else 'D'
def contact(a,b,c,d):
 oa,ob=ori(a,b),ori(c,d)
 if 'D' in (oa,ob):return False
 if oa==ob=='H':return abs(a[1]-c[1])<1e-7 and max(min(a[0],b[0]),min(c[0],d[0]))<=min(max(a[0],b[0]),max(c[0],d[0]))+1e-7
 if oa==ob=='V':return abs(a[0]-c[0])<1e-7 and max(min(a[1],b[1]),min(c[1],d[1]))<=min(max(a[1],b[1]),max(c[1],d[1]))+1e-7
 if oa=='V':return contact(c,d,a,b)
 x=c[0];y=a[1];return min(a[0],b[0])-1e-7<=x<=max(a[0],b[0])+1e-7 and min(c[1],d[1])-1e-7<=y<=max(c[1],d[1])+1e-7
def proper(a,b,c,d):
 oa,ob=ori(a,b),ori(c,d)
 if {oa,ob}!={'H','V'}:return False
 if oa=='V':a,b,c,d=c,d,a,b
 x=c[0];y=a[1];return min(a[0],b[0])<x<max(a[0],b[0]) and min(c[1],d[1])<y<max(c[1],d[1])
def inside(a,b,n):
 x1,y1=a;x2,y2=b;l,t,r,bt=box(n)
 if abs(y1-y2)<1e-7:return t+1e-7<y1<bt-1e-7 and max(min(x1,x2),l)<min(max(x1,x2),r)-1e-7
 x=x1;return l+1e-7<x<r-1e-7 and max(min(y1,y2),t)<min(max(y1,y2),bt)-1e-7
frozen={r['id']:r for r in cand['routes'] if r.get('planningStatus')=='FROZEN_FROM_C4E1'}
def path(r,pars):
 s=port(nodes[r['source']],r['sourceSide'],r['sourcePortFraction']);t=port(nodes[r['target']],r['targetSide'],r['targetPortFraction']);x1,x2,y=pars[r['id']]
 p=[s,(x1,s[1]),(x1,y),(x2,y),(x2,t[1]),t]
 q=[p[0]]
 for z in p[1:]:
  if z!=q[-1]:q.append(z)
 return q
def score(pars):
 paths={k:[port(nodes[v['source']],v['sourceSide'],v['sourcePortFraction']),*map(tuple,v['waypoints']),port(nodes[v['target']],v['targetSide'],v['targetPortFraction'])] for k,v in frozen.items()}
 for r in cand['routes']:
  if r['id'] not in frozen:paths[r['id']]=path(r,pars)
 contacts=0;cross=0;nodesbad=0;short=0;red=0
 ids=list(paths)
 for i,a in enumerate(ids):
  for b in ids[i+1:]:
   for sa,sb in segs(paths[a]):
    for sc,sd in segs(paths[b]):
     if contact(sa,sb,sc,sd):contacts+=1
     if proper(sa,sb,sc,sd):cross+=1
 for rid,p in paths.items():
  for a,b in segs(p):
   if math.hypot(a[0]-b[0],a[1]-b[1])<.1-1e-7:short+=1
  for a,b,c in zip(p,p[1:],p[2:]):
   if (abs(a[0]-b[0])<1e-7 and abs(b[0]-c[0])<1e-7) or (abs(a[1]-b[1])<1e-7 and abs(b[1]-c[1])<1e-7):red+=1
  r=next(x for x in cand['routes'] if x['id']==rid)
  for a,b in segs(p):
   for nid,n in nodes.items():
    if nid not in (r['source'],r['target']) and inside(a,b,n):nodesbad+=1
 return contacts*100+cross*10+nodesbad*100+short*10+red, (contacts,cross,nodesbad,short,red), paths
todo=[r for r in cand['routes'] if r['id'] not in frozen]
def init():
 pars={}
 # top/bottom route lanes fixed by random assignment; x1/x2 in side-safe corridors
 leftx=[4.55+i*.17 for i in range(9)];rightx=[29.25-i*.17 for i in range(9)]
 random.shuffle(leftx);random.shuffle(rightx)
 for i,r in enumerate(todo):
  sx=leftx[i%9] if r['sourceSide']=='RIGHT' else rightx[i%9]
  # sourceSide LEFT means right actors; target x stage from target side
  target=nodes[r['target']]; b=box(target)
  if r['targetSide']=='LEFT': tx=b[0]-0.15
  else: tx=b[2]+0.15
  pars[r['id']]=(sx,tx,random.choice([1.0,1.5,2.0,2.5,3.0,16.0,16.5,17.0,17.5,18.0]))
 return pars
best=(10**9,None,None)
for restart in range(5):
 p=init();cur=score(p)[0]
 for it in range(500):
  q={**p};rid=random.choice(list(q));x1,x2,y=q[rid];choice=random.randrange(3)
  if choice==0:x1=max(4.5,min(29.5,x1+random.uniform(-.35,.35)))
  elif choice==1:x2=max(7.0,min(26.5,x2+random.uniform(-.35,.35)))
  else:y=max(.5,min(18.5,y+random.uniform(-.5,.5)))
  q[rid]=(x1,x2,y);ns=score(q)[0]
  if ns<=cur or random.random()<math.exp((cur-ns)/(20*(1-it/500)+.01)):
   p,cur=q,ns
  if cur<best[0]:
   best=(cur,p,score(p)[1]);print('BEST',best[0],best[2],restart,it)
   if best[2][0]==0 and best[2][1]==0 and best[2][2]==0 and best[2][3]==0 and best[2][4]==0:
    score(p);Path(r'D:\moodle\candidate-search-best.txt').write_text(repr(p),encoding='utf-8');raise SystemExit
print('FINAL',best[0],best[2]);print(best[1])
