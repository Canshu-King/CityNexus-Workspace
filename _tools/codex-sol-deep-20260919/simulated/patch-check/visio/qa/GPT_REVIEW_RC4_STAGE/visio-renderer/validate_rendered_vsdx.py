"""Independent package/XML validator for rendered VSDX."""
import argparse,zipfile,re,os,json,yaml,xml.etree.ElementTree as ET
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('vsdx'); ap.add_argument('--spec-dir',default=os.path.join(os.path.dirname(__file__),'..','visio-spec','pages')); ap.add_argument('--page',required=True); a=ap.parse_args()
    d=yaml.safe_load(open(os.path.join(a.spec_dir,a.page+'.yaml'),encoding='utf8')); failures=[]
    page_index={'00_style_guide':1,'p1_uc_overview':2,'p1_domain_overview':3}.get(a.page,1)
    with zipfile.ZipFile(a.vsdx) as z: blobs=[z.read(n) for n in z.namelist() if n.endswith('.xml') and (n==f'visio/pages/page{page_index}.xml' or n=='visio/document.xml')]
    xml=b'\n'.join(blobs).decode('utf8','ignore');
    for bad in ('#VALUE!','#REF!'):
        if bad in xml: failures.append('forbidden '+bad)
    expected={str(x['id']) for x in d.get('shapes',[])}|{str(x['id']) for x in d.get('connectors',[])}
    actual=set(re.findall(r"N=['\"]SpecId['\"][^>]*>.*?N=['\"]Value['\"]\s+V=['\"]([^'\"]+)['\"]",xml,re.S))
    if not expected: failures.append('empty YAML semantics')
    actual={x for x in actual if not x.startswith('HDR-') and not x.startswith('PRES-') and x!='BG-CANVAS' and x!='LEGEND'}
    missing=sorted(expected-actual); extra=sorted(actual-expected)
    if missing: failures.append('missing SpecId: '+','.join(missing))
    if extra: failures.append('unexpected SpecId: '+','.join(extra))
    result={'status':'PASS' if not failures else 'FAIL','page':a.page,'expectedSpecIds':sorted(expected),'actualSpecIds':sorted(actual),'failures':failures}
    print(json.dumps(result,ensure_ascii=False,indent=2)); return 0 if not failures else 1
if __name__=='__main__': raise SystemExit(main())
