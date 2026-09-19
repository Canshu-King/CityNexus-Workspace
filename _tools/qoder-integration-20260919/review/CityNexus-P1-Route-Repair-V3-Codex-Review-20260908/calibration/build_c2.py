import os,sys,win32com.client,yaml
sys.path.insert(0,os.path.abspath(os.path.join(os.path.dirname(__file__),'..')))
from render_core import set_prop,resolve_font_id,load_master_map
from style_adapter import apply_style
ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),'..','..')); OUT=os.path.join(os.path.dirname(__file__),'out')
def main():
 tokens=yaml.safe_load(open(os.path.join(ROOT,'visio-spec','style-tokens.yaml'),encoding='utf8')); mm=load_master_map(os.path.join(ROOT,'visio-renderer','native-master-map.json')); a=win32com.client.Dispatch('Visio.Application'); a.Visible=False; a.AlertResponse=7; d=a.Documents.Add(''); p=d.Pages.Item(1); p.NameU='C2_Native_Class'; p.PageSheet.CellsU('PageWidth').FormulaU='12 in'; p.PageSheet.CellsU('PageHeight').FormulaU='8 in'; fid=resolve_font_id(d); st=a.Documents.OpenEx(mm['stencils']['Class']['stencil'],66); m=st.Masters.ItemU('Class'); warnings=[]
 try:
  for sid,ref,name,fields,x in [('C2-JOURNEY','classJourney','Journey',['journeyId','lifecycleState','healthStatus'],3.5),('C2-JOURNEY-TWIN','classProjection','JourneyTwin',['healthStatus','riskScore'],8.5)]:
   sh=p.Drop(m,x,4.5); sh.Text=name; set_prop(sh,'SpecId',sid); set_prop(sh,'StyleRef',ref); apply_style(sh,sid,ref,tokens,fid,warnings)
   for j,text in enumerate((["<<aggregate root>>"] if name=='Journey' else ["<<projection>>"])+fields):
    ov=p.DrawRectangle(x-1.4,6.4-j*0.35,x+1.4,6.65-j*0.35); ov.Text=text; set_prop(ov,'SpecId',sid+'-OVERLAY-'+str(j)); set_prop(ov,'Role','presentation'); set_prop(ov,'OwnerSpecId',sid); set_prop(ov,'ContentRole','stereotype' if j==0 else 'field'); ov.CellsU('Char.Font').FormulaU=str(fid); ov.CellsU('Char.Color').FormulaU='RGB(15,23,42)'; ov.CellsU('LinePattern').FormulaU='0'; ov.CellsU('FillForegnd').FormulaU='RGB(255,255,255)'
  for i in range(1,p.Shapes.Count+1):
   s=p.Shapes.Item(i)
   if '成员名' in str(s.Text) or '类名' in str(s.Text): s.Text=''
  f=os.path.join(OUT,'C2_Native_Class.vsdx'); d.SaveAs(f); p.Export(os.path.join(OUT,'C2_Native_Class.raw.svg')); p.Export(os.path.join(OUT,'C2_Native_Class.png')); print(f)
 finally: st.Close(); d.Close(); a.Quit()
if __name__=='__main__': main()
