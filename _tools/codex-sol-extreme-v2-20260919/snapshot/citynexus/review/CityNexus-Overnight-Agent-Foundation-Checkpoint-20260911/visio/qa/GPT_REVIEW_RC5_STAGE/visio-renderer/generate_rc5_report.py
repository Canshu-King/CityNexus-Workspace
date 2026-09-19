import os,subprocess,sys,json
root=os.path.abspath(os.path.join(os.path.dirname(__file__),'..')); vs=os.path.join(root,'visio','CityNexus_Visio_Model_Baseline_v1.0.4_RC5.vsdx')
pages=['00_style_guide','p1_uc_overview','p1_domain_overview']; out={'release':'v1.0.4-RC5','pages':{},'status':'PASS','failures':[]}
for p in pages:
    r=subprocess.run([sys.executable,os.path.join(root,'visio-renderer','validate_rendered_vsdx.py'),vs,'--page',p],capture_output=True,text=True); j=json.loads(r.stdout); out['pages'][p]=j
    if j.get('status')!='PASS': out['status']='FAIL'; out['failures']+=j.get('failures',[])
for p in pages:
    n={'00_style_guide':'00_Style_Guide','p1_uc_overview':'P1_UC_Overview','p1_domain_overview':'P1_Domain_Overview'}[p]
    svg=os.path.join(root,'visio','exports','phase1-rc5',n+'_v1.0.4-RC5.svg')
    r=subprocess.run([sys.executable,os.path.join(root,'visio-renderer','validate_rendered_svg.py'),svg],capture_output=True,text=True); j=json.loads(r.stdout); out.setdefault('svg',{})[p]=j
    if j.get('status')!='PASS': out['status']='FAIL'; out['failures']+=j.get('failures',[])
out['artifacts']={'vsdx':'visio/CityNexus_Visio_Model_Baseline_v1.0.4_RC5.vsdx','svg':'visio/exports/phase1-rc5','png':'visio/exports/phase1-rc5','renderer':'visio-renderer'}
json.dump(out,open(os.path.join(root,'visio','qa','phase1-render-report-v1.0.4-RC5.json'),'w',encoding='utf8'),ensure_ascii=False,indent=2)
print(json.dumps({'status':out['status'],'report':'visio/qa/phase1-render-report-v1.0.4-RC5.json'},ensure_ascii=False))
