"""Renderer v0.3.1 C1-only calibration build. Never reads formal exports."""
import json, os, subprocess, sys, yaml, win32com.client
from render_core import load_master_map, set_prop, resolve_font_id
from style_adapter import apply_style
ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),'..')); OUT=os.path.join(os.path.dirname(__file__),'calibration','out')


def write_summary(status):
    with open(os.path.join(OUT, 'calibration-summary.json'), 'w', encoding='utf8') as handle:
        json.dump({'C1': status, 'C2': 'BLOCKED', 'C3': 'BLOCKED', 'C4': 'BLOCKED'}, handle, indent=2)


def main():
 os.makedirs(OUT,exist_ok=True)
 # Static tests are a hard gate and are always regenerated.
 test_dir=os.path.join(os.path.dirname(__file__),'tests'); tr=subprocess.run([sys.executable,'-m','pytest',test_dir,'-q'],cwd=ROOT,capture_output=True,text=True)
 json.dump({'status':'PASS' if tr.returncode==0 else 'FAIL','stdout':tr.stdout,'stderr':tr.stderr},open(os.path.join(OUT,'static-test-report.json'),'w',encoding='utf8'),ensure_ascii=False,indent=2)
 if tr.returncode!=0:
  write_summary('FAIL'); raise SystemExit(tr.returncode)
 token_path=os.path.join(ROOT,'visio-spec','style-tokens.yaml')
 map_path=os.path.join(os.path.dirname(__file__),'native-master-map.json')
 tokens=yaml.safe_load(open(token_path,encoding='utf8'))
 master_map=load_master_map(map_path)
 app=win32com.client.Dispatch('Visio.Application'); app.Visible=False; app.AlertResponse=7
 doc=app.Documents.Add(''); page=doc.Pages.Item(1); page.NameU='C1_Font_Style'
 page.PageSheet.CellsU('PageWidth').FormulaU='12 in'; page.PageSheet.CellsU('PageHeight').FormulaU='9 in'
 page.PageSheet.CellsU('FillForegnd').FormulaU='RGB(248,250,252)'
 fid=resolve_font_id(doc)
 base=os.path.dirname(master_map['stencils']['Actor']['stencil'])
 use=app.Documents.OpenEx(master_map['stencils']['Actor']['stencil'],66)
 cls=app.Documents.OpenEx(master_map['stencils']['Class']['stencil'],66)
 masters={'actor':use.Masters.ItemU(master_map['stencils']['Actor']['masterNameU']), 'use':use.Masters.ItemU(master_map['stencils']['Use Case']['masterNameU']), 'class':cls.Masters.ItemU(master_map['stencils']['Class']['masterNameU'])}
 samples=[('C1-ACTOR-H','actorHuman','actor'),('C1-ACTOR-E','actorExternal','actor'),('C1-UC-DEFAULT','useCaseDefault','use'),('C1-UC-PLANNING','useCasePlanning','use'),('C1-UC-COMMERCE','useCaseCommerce','use'),('C1-CLASS-DEFAULT','classDefault','class'),('C1-CLASS-JOURNEY','classJourney','class'),('C1-CLASS-PROJECTION','classProjection','class'),('C1-CLASS-PLANNING','classPlanning','class'),('C1-CLASS-COMMERCE','classCommerce','class'),('C1-CLASS-EVENT','classEvent','class')]
 warnings=[]
 try:
  for i,(sid,ref,kind) in enumerate(samples):
   sh=page.Drop(masters[kind],1.4+(i%4)*2.7,7.2-(i//4)*2.6); sh.Text=ref
   set_prop(sh,'SpecId',sid); set_prop(sh,'StyleRef',ref); apply_style(sh,sid,ref,tokens,fid,warnings)
  # Remove localized default member placeholders emitted as sibling shapes by
  # the native Class master; never alter the semantic class body.
  for i in range(1,page.Shapes.Count+1):
   s=page.Shapes.Item(i)
   if '成员名' in str(s.Text) or '类名' in str(s.Text):
    s.Text=''
  f=os.path.join(OUT,'C1_Font_Style.vsdx'); doc.SaveAs(f); page.Export(os.path.join(OUT,'C1_Font_Style.raw.svg')); page.Export(os.path.join(OUT,'C1_Font_Style.png'))
  validator=os.path.join(os.path.dirname(__file__),'calibration','validate_c1.py')
  completed=subprocess.run([sys.executable,validator],cwd=ROOT)
  write_summary('PASS' if completed.returncode == 0 else 'FAIL')
  if completed.returncode:
   raise SystemExit(completed.returncode)
  print(f)
 finally:
  use.Close(); cls.Close(); doc.Close(); app.Quit()
if __name__=='__main__': main()
