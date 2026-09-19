import os,json,re
HERE=os.path.dirname(__file__); OUT=os.path.join(HERE,'out'); S=os.path.join(OUT,'C2_Native_Class.raw.svg')
def main():
 s=open(S,encoding='utf8',errors='ignore').read() if os.path.exists(S) else ''; visible=' '.join(re.findall(r'<text[^>]*>(.*?)</text>',s,re.I|re.S)); req=['Journey','aggregate root','journeyId','lifecycleState','healthStatus','JourneyTwin','projection','riskScore']; failures=[x for x in req if x not in visible]+[x for x in ('成员名','-成员名','类名','Calibri','SimSun','宋体') if x in visible]+(['linearGradient'] if '<linearGradient' in s else []); r={'calibration':'C2','implementation':'native-class-plus-presentation-overlay','requiredText':req,'status':'PASS' if not failures else 'FAIL','failures':failures}; json.dump(r,open(os.path.join(OUT,'C2_Native_Class-report.json'),'w'),ensure_ascii=False,indent=2); print(json.dumps(r,ensure_ascii=False,indent=2)); return 0 if not failures else 1
if __name__=='__main__': raise SystemExit(main())
