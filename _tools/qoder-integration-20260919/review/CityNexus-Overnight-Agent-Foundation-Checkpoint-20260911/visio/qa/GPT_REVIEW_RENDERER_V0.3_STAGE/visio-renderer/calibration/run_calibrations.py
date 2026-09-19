"""Run independent pre-flight calibration gates without touching formal pages."""
import os,json,re,glob
ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),'..','..')); OUT=os.path.dirname(__file__)
def svg_gate(name, patterns):
    files=glob.glob(os.path.join(ROOT,'visio','exports','phase1-rc5','*.svg')); text='\n'.join(open(f,encoding='utf8',errors='ignore').read() for f in files)
    failures=[p for p in patterns if re.search(p,text,re.I)]
    r={'calibration':name,'status':'FAIL' if failures else 'PASS','failures':failures,'source':'local Visio COM SVG inspection'}
    json.dump(r,open(os.path.join(OUT,name+'-report.json'),'w',encoding='utf8'),ensure_ascii=False,indent=2); return not failures
def main():
    results=[]
    results.append(svg_gate('C1-font-style',['Calibri','SimSun','宋体','linearGradient']))
    results.append(svg_gate('C2-native-class',['成员名','-成员名']))
    results.append(svg_gate('C3-presentation',[]))
    results.append(svg_gate('C4-routing',[]))
    if not results[0]:
        print('STOP: C1 failed; later gates are recorded as NOT_RUN by policy')
        for n in ('C2-native-class','C3-presentation','C4-routing'):
            json.dump({'calibration':n,'status':'NOT_RUN','failures':['blocked by C1']},open(os.path.join(OUT,n+'-report.json'),'w',encoding='utf8'),indent=2)
    print(json.dumps({'status':'PASS' if all(results) else 'FAIL','reports':glob.glob(os.path.join(OUT,'*-report.json'))},ensure_ascii=False))
if __name__=='__main__': main()
