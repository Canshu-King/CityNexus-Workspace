import os,sys,win32com.client,yaml,json
sys.path.insert(0,os.path.abspath(os.path.join(os.path.dirname(__file__),'..')))
from render_core import set_prop,resolve_font_id,load_master_map
from style_adapter import apply_style
ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),'..','..')); OUT=os.path.join(os.path.dirname(__file__),'out')
def force(cell,formula):
 try: cell.FormulaForceU=formula
 except Exception: cell.FormulaU=formula
def all_shapes(coll):
 for i in range(1,coll.Count+1):
  s=coll.Item(i); yield s
  try: yield from all_shapes(s.Shapes)
  except Exception: pass
def main():
 tokens=yaml.safe_load(open(os.path.join(ROOT,'visio-spec','style-tokens.yaml'),encoding='utf8')); mm=load_master_map(os.path.join(ROOT,'visio-renderer','native-master-map.json')); a=win32com.client.Dispatch('Visio.Application'); a.Visible=False; a.AlertResponse=7; d=a.Documents.Add(''); p=d.Pages.Item(1); p.NameU='C2_Anchored_Class_v2'; fid=resolve_font_id(d); st=a.Documents.OpenEx(mm['stencils']['Class']['stencil'],66); m=st.Masters.ItemU('Class'); owners=[]; overlays=[]
 try:
  for sid,ref,name,fields,x in [('C2-JOURNEY','classJourney','Journey',['journeyId','lifecycleState','healthStatus'],3.5),('C2-JOURNEY-TWIN','classProjection','JourneyTwin',['healthStatus','riskScore'],8.5)]:
   sh=p.Drop(m,x,4.5); sh.Text=name; set_prop(sh,'SpecId',sid); set_prop(sh,'StyleRef',ref); apply_style(sh,sid,ref,tokens,fid,[])
   owner_id=sh.ID; owners.append((sid,sh,fields))
   # Use native stereotype capability discovered in the local master.
   try: force(sh.CellsU('User.StereoType'),'TRUE')
   except Exception: pass
   found=False
   for i in range(1,sh.Shapes.Count+1):
    ch=sh.Shapes.Item(i)
    try:
     if ch.CellExistsU('User.StereoType',0): force(ch.CellsU('User.StereoType'),'TRUE'); ch.Text='<<aggregate root>>' if name=='Journey' else '<<projection>>'; found=True
    except Exception: pass
   if not found: pass
   for order,text in enumerate(fields,1):
    ov=p.DrawRectangle(x-1.25,4.25-(order-1)*0.22,x+1.25,4.43-(order-1)*0.22); ov.Text=text; set_prop(ov,'SpecId',sid+'-FIELD-'+str(order)); set_prop(ov,'Role','presentation'); set_prop(ov,'OwnerSpecId',sid); set_prop(ov,'ContentRole','field'); set_prop(ov,'FieldOrder',order)
    # Formula-linked geometry follows owner movement and resize.
    force(ov.CellsU('PinX'),f'Sheet.{owner_id}!PinX'); force(ov.CellsU('Width'),f'Sheet.{owner_id}!Width-0.16 in'); force(ov.CellsU('Height'),'0.18 in'); force(ov.CellsU('PinY'),f'Sheet.{owner_id}!PinY+Sheet.{owner_id}!Height*0.18-{(order-1)*0.22} in'); force(ov.CellsU('FillPattern'),'0'); force(ov.CellsU('LinePattern'),'0'); force(ov.CellsU('Char.Font'),str(fid)); overlays.append((sid,sh,ov))
  # Resolve native stereotype text siblings and clear default localized placeholders.
  stereo=[s for s in all_shapes(p.Shapes) if '构造型' in str(s.Text)]
  if len(stereo)>=2:
   stereo[0].Text='<<aggregate root>>'; stereo[1].Text='<<projection>>'
  for s in all_shapes(p.Shapes):
   if '成员名' in str(s.Text) or '类名' in str(s.Text): s.Text=''
  # Live anchor test: move each owner and verify linked overlays move identically.
  anchor=[]
  for sid,owner,ov in overlays:
   ox,oy=float(owner.CellsU('PinX').Result('inches')),float(owner.CellsU('PinY').Result('inches')); vx,vy=float(ov.CellsU('PinX').Result('inches')),float(ov.CellsU('PinY').Result('inches')); owner.CellsU('PinX').FormulaU=f'{ox+20/25.4} in'; owner.CellsU('PinY').FormulaU=f'{oy+10/25.4} in'; nx,ny=float(ov.CellsU('PinX').Result('inches')),float(ov.CellsU('PinY').Result('inches')); anchor.append({'owner':sid,'deltaErrorMm':max(abs((nx-vx)-(20/25.4))*25.4,abs((ny-vy)-(10/25.4))*25.4)}); owner.CellsU('PinX').FormulaU=f'{ox} in'; owner.CellsU('PinY').FormulaU=f'{oy} in'
  f=os.path.join(OUT,'C2_Anchored_Class_v2.vsdx'); d.SaveAs(f); p.Export(os.path.join(OUT,'C2_Anchored_Class_v2.raw.svg')); p.Export(os.path.join(OUT,'C2_Anchored_Class_v2.png')); json.dump({'calibration':'C2.1','implementation':'native-class-plus-presentation-overlay','anchorBehaviour':'PASS' if max(x['deltaErrorMm'] for x in anchor)<=0.5 else 'FAIL','anchorTests':anchor},open(os.path.join(OUT,'C2_Anchored_Class_v2-report.json'),'w'),indent=2); print(f)
 finally: st.Close(); d.Close(); a.Quit()
if __name__=='__main__': main()
