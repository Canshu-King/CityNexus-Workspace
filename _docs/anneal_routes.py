import yaml,random,math,copy
from pathlib import Path
R=Path(r'D:\moodle\CityNexus\visio-renderer'); sem=yaml.safe_load((R.parent/'visio-spec/pages/p1_uc_overview.yaml').read_text(encoding='utf8')); base=yaml.safe_load((R/'phase1-routing-rc6-candidate.yaml').read_text(encoding='utf8')); nodes={s['id']:s for s in sem['shapes'] if s['id']!='BOUNDARY'}
def box(n):return(n['x']-n['width']/2,n['y']-n['height']/2,n['x']+n['width']/2,n['y']+n['height']/2)
def port(n,s,f):
 l,t,r,b=box(n);f=float(f);return {'LEFT':(l,t+(b-t)*f),'RIGHT':(r,t+(b-t)*f),'TOP':(l+(r-l)*f,t),'BOTTOM':(l+(r-l)*f,b)}[s]
def path(r):return [port(nodes[r['source']],r['sourceSide'],r['sourcePortFraction']),*map(tuple,r.get('waypoints') or []),port(nodes[r['target']],r['targetSide'],r['targetPortFraction'])]
def simp(p):
 q=[p[0]]
 for x in p[1:]:
  if x==q[-1]:continue
  if len(q)>1 and ((q[-2][0]==q[-1][0]==x[0])or(q[-2][1]==q[-1][1]==x[1])):q[-1]=x
  else:q.append(x)
 return q
def ori(a,b):return 'H' if abs(a[1]-b[1])<1e-8 else 'V' if abs(a[0]-b[0])<1e-8 else 'D'
def contact(a,b,c,d):
 oa,ob=ori(a,b),ori(c,d)
 if 'D'in(oa,ob):return 0
 if oa==ob=='H':
  return abs(a[1]-c[1])<1e-8 and max(min(a[0],b[0]),min(c[0],d[0]))<=min(max(a[0],b[0]),max(c[0],d[0]))+1e-8
 if oa==ob=='V':
  return abs(a[0]-c[0])<1e-8 and max(min(a[1],b[1]),min(c[1],d[1]))<=min(max(a[1],b[1]),max(c[1],d[1]))+1e-8
 if oa=='V':return contact(c,d,a,b)
 return min(a[0],b[0])-1e-8<=c[0]<=max(a[0],b[0])+1e-8 and min(c[1],d[1])-1e-8<=a[1]<=max(c[1],d[1])+1e-8
def score(paths):
 ids=list(paths);cont=cross=short=red=0
 for i,a in enumerate(ids):
  pa=paths[a]
  for b in ids[i+1:]:
   pb=paths[b]
   for sa in zip(pa,pa[1:]):
    for sb in zip(pb,pb[1:]):
     if contact(*sa,*sb):cont+=1
  for u,v in zip(pa,pa[1:]):
   if ori(u,v)=='D':cross+=10
   if math.hypot(v[0]-u[0],v[1]-u[1])<.1-1e-9:short+=1
  for j in range(1,len(pa)-1):
   if (pa[j-1][0]==pa[j][0]==pa[j+1][0])or(pa[j-1][1]==pa[j][1]==pa[j+1][1]):red+=1
 return cont+cross+short+red,(cont,cross,short,red)
routes={r['id']:r for r in base['routes']};paths={k:simp(path(v)) for k,v in routes.items()};mutable=[k for k,v in routes.items() if v.get('planningStatus')!='FROZEN_FROM_C4E1'];rng=random.Random(9);best,bdet=score(paths);bp=copy.deepcopy(paths);print('start',best,bdet)
for restart in range(100):
 cur=copy.deepcopy(paths);cs,_=score(cur)
 for it in range(3000):
  rid=rng.choice(mutable);p=cur[rid];
  if len(p)<3:continue
  i=rng.randrange(1,len(p)-1);a,b=p[i-1],p[i+1];z=list(p[i]);o1,o2=ori(a,p[i]),ori(p[i],b)
  if o1=='H' and o2=='V':z[0]+=rng.choice([-0.3,-0.2,-0.1,0.1,0.2,0.3])
  elif o1=='V' and o2=='H':z[1]+=rng.choice([-0.3,-0.2,-0.1,0.1,0.2,0.3])
  else:continue
  np=copy.deepcopy(cur);np[rid]=p[:i]+[tuple(z)]+p[i+1:];ns,det=score(np);temp=max(.05,3*(1-it/3000))
  if ns<=cs or rng.random()<math.exp((cs-ns)/temp):cur,cs=np,ns
  if ns<best:best,bdet,bp=ns,det,copy.deepcopy(np);print('BEST',best,bdet,restart,it)
  if bdet[0]==0 and bdet[2]==0 and bdet[3]==0:
   out=copy.deepcopy(base)
   for rr in out['routes']:
    if rr['id'] in bp and rr.get('planningStatus')!='FROZEN_FROM_C4E1':rr['waypoints']=[[float(x),float(y)] for x,y in bp[rr['id']][1:-1]];rr['planningStatus']='ROUTE_PLANNED_PENDING_EXTERNAL_FREEZE'
   Path(r'D:\moodle\candidate-annealed.yaml').write_text(yaml.safe_dump(out,sort_keys=False,allow_unicode=True),encoding='utf8');print('FOUND');raise SystemExit
print('DONE',best,bdet)
