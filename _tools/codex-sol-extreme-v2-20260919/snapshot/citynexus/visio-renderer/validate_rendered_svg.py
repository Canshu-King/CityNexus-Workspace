import argparse,os,re,json
def main():
 p=argparse.ArgumentParser(); p.add_argument('svg'); a=p.parse_args(); s=open(a.svg,encoding='utf8',errors='ignore').read(); f=[]
 for x in ('#VALUE!','#REF!','成员名','SimSun','宋体','Calibri'): 
  if x in s:f.append('forbidden '+x)
 for x in ('linearGradient','filter'):
  if ('<'+x) in s:f.append('forbidden element '+x)
 for x in ('Segoe UI','F8FAFC'):
  if x.lower() not in s.lower(): f.append('missing '+x)
 out={'status':'PASS' if not f else 'FAIL','failures':f,'bytes':len(s)}; print(json.dumps(out,ensure_ascii=False,indent=2)); return 0 if not f else 1
if __name__=='__main__': raise SystemExit(main())
