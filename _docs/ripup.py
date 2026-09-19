# generate backtracking router from grid10 helpers
exec(open(r'D:\grid10_search.py',encoding='utf8').read().split('best=0')[0])
import random,time
# order prioritized route families / endpoints
order=sorted(assoc,key=lambda r:(r['family']!='traveler',r['target']))
# recursive search with MRV: choose unplaced route with smallest quick path availability (3 seeds)
def search(paths,remaining,depth=0,limit_depth=4):
 if not remaining:return paths
 # pick route with fewest candidate paths from quick trials
 choices=[]
 for r in remaining:
  ps=[]
  for seed in range(3):
   p=astar(r,paths,depth*10000+seed)
   if p:ps.append(p)
  choices.append((len(ps),r,ps))
 choices.sort(key=lambda x:x[0]); k,r,ps=choices[0]
 if not ps:return None
 # sort candidates by length
 for p in ps:
  np=dict(paths);np[r['id']]=p
  res=search(np,[z for z in remaining if z['id']!=r['id']],depth+1,limit_depth)
  if res:return res
 return None
# iterative random greedy + ripup
best=0;bestpaths=None;start=time.time()
for trial in range(300):
 paths=fpaths(); rem=list(assoc); rng=random.Random(trial)
 while rem:
  # route one with random order
  rng.shuffle(rem); placed=False
  for idx,r in enumerate(rem):
   p=astar(r,paths,trial*100+idx)
   if p:paths[r['id']]=p; rem.remove(r);placed=True;break
  if not placed:
   break
 good=len(paths)-len(frozen)
 if good>best:best=good;bestpaths=paths;print('BEST',best,'trial',trial,flush=True)
 if good==len(assoc):
  print('FOUND');out=yaml.safe_load((R/'phase1-routing-rc6-candidate.yaml').read_text(encoding='utf8'))
  for rr in out['routes']:
   if rr['id'] in paths and rr.get('planningStatus')!='FROZEN_FROM_C4E1':rr['waypoints']=[[x,y] for x,y in paths[rr['id']][1:-1]];rr['planningStatus']='ROUTE_PLANNED_PENDING_EXTERNAL_FREEZE'
  Path(r'D:\moodle\candidate-grid-found.yaml').write_text(yaml.safe_dump(out,sort_keys=False,allow_unicode=True),encoding='utf8');break
 if time.time()-start>240:break
print('DONE',best,flush=True)
