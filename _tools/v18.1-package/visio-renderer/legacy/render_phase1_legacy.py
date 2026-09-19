"""Deterministic YAML -> native Visio Phase 1 renderer."""
import argparse, os, sys, yaml, win32com.client

ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
SPEC=os.path.join(ROOT,'visio-spec','pages')
VISIO_DIR=os.path.join(ROOT,'visio')
TEMPLATE=os.path.join(os.environ.get('ProgramFiles','C:/Program Files'),'Microsoft Office','root','Office16','Visio Content','2052','UUSEME_M.VSTX')
USE_STENCIL=os.path.join(os.environ.get('ProgramFiles','C:/Program Files'),'Microsoft Office','root','Office16','Visio Content','2052','UUSEME_M.VSSX')
CLASS_STENCIL=os.path.join(os.environ.get('ProgramFiles','C:/Program Files'),'Microsoft Office','root','Office16','Visio Content','2052','USTRME_M.VSSX')

def xy(x,y,h): return x/2.54,(h-y)/2.54
def prop(shape, value):
    try:
        if not shape.CellExistsU('Prop.SpecId',0): shape.AddNamedRow(243,'SpecId',0)
        shape.CellsU('Prop.SpecId').FormulaU='"%s"'%value
    except Exception: pass
def font(shape, fid):
    try: shape.CellsU('Char.Font').FormulaU=str(fid)
    except Exception: pass
def render(page_file, doc, app, page):
    data=yaml.safe_load(open(page_file,encoding='utf-8')); h=float(data['pageHeight']); page.NameU=data['pageName']
    page.PageSheet.CellsU('PageWidth').FormulaU=str(float(data['pageWidth'])/2.54)+' in'; page.PageSheet.CellsU('PageHeight').FormulaU=str(h/2.54)+' in'
    page.PageSheet.CellsU('FillForegnd').FormulaU='RGB(248,250,252)'
    use=doc.Application.Documents.OpenEx(USE_STENCIL,66); cls=doc.Application.Documents.OpenEx(CLASS_STENCIL,66)
    masters={'uml_actor':use.Masters.ItemU('Actor'),'uml_use_case':use.Masters.ItemU('Use Case'),'uml_subsystem':use.Masters.ItemU('Subsystem'),'uml_class':cls.Masters.ItemU('Class')}
    font_id=next((i for i in range(1,doc.Fonts.Count+1) if doc.Fonts.Item(i).Name=='Segoe UI'),228)
    idx={}
    for s in data.get('shapes',[]):
        x,y=xy(float(s['x']),float(s['y']),h); sh=page.Drop(masters[s['type']],x,y); sh.Text=s.get('text',''); prop(sh,s['id']); font(sh,font_id); idx[s['id']]=sh
        sh.CellsU('Width').FormulaU=str(float(s['width'])/2.54)+' in'; sh.CellsU('Height').FormulaU=str(float(s['height'])/2.54)+' in'; sh.CellsU('PinX').FormulaU=str(x)+' in'; sh.CellsU('PinY').FormulaU=str(y)+' in'
    for c in data.get('connectors',[]):
        cm={'association':'Association','dependency':'Dependency','composition':'Composition','extend':'Extend'}[c['type']]
        st=use if c['type'] in ('association','extend') else cls
        sh=page.Drop(st.Masters.ItemU(cm),0,0); prop(sh,c['id']); font(sh,font_id); sh.CellsU('BeginX').GlueTo(idx[c['source']].CellsU('PinX')); sh.CellsU('EndX').GlueTo(idx[c['target']].CellsU('PinX'))
        if c.get('label'): sh.Text=c['label']+'\n'+c.get('condition','')
        # Endpoint multiplicities are independent presentation labels.
        for endpoint, key in (('source','sourceMultiplicity'),('target','targetMultiplicity')):
            if key in c:
                ref = idx[c[endpoint]]
                px=float(ref.CellsU('PinX').Result('inches')); py=float(ref.CellsU('PinY').Result('inches'))
                dx = -0.18 if endpoint=='source' else 0.18
                lab=page.DrawRectangle(px+dx-0.18,py+0.08,px+dx+0.18,py+0.28); lab.Text=str(c[key]); prop(lab,'PRES-MULT-'+c['id']+'-'+endpoint); font(lab,font_id)
                try:
                    lab.AddNamedRow(243,'Role',0); lab.CellsU('Prop.Role').FormulaU='"presentation"'; lab.CellsU('FillForegnd').FormulaU='RGB(248,250,252)'; lab.CellsU('LinePattern').FormulaU='0'
                except Exception: pass
    # Presentation layer (excluded from semantic counts).
    for role,text,x1,y1,x2,y2 in [('HDR-TITLE',data.get('title',''),0.3,h/2.54-0.35,12.8,h/2.54-0.05),('HDR-SUBTITLE',data.get('subtitle',''),0.3,h/2.54-0.65,12.8,h/2.54-0.38),('HDR-STATUS',data.get('statusTag',''),10.5,h/2.54-0.65,13.0,h/2.54-0.38)]:
        if text:
            sh=page.DrawRectangle(x1,y1,x2,y2); sh.Text=text; prop(sh,role); font(sh,font_id)
            try: sh.AddNamedRow(243,'Role',0); sh.CellsU('Prop.Role').FormulaU='"presentation"'; sh.CellsU('FillForegnd').FormulaU='RGB(248,250,252)'; sh.CellsU('LinePattern').FormulaU='0'
            except Exception: pass
    lg=data.get('legend')
    if lg:
        lx,ly,lw,lh=[float(lg[k])/2.54 for k in ('x','y','width','height')]
        ly=(h-float(lg['y']))/2.54
        legend_text='LEGEND\n'+' • '.join(str(i) for i in lg.get('items',[]))
        sh=page.DrawRectangle(lx,ly,lx+lw,ly+lh); sh.Text=legend_text; prop(sh,'LEGEND'); font(sh,font_id)
        try:
            sh.AddNamedRow(243,'Role',0); sh.CellsU('Prop.Role').FormulaU='"presentation"'; sh.CellsU('FillForegnd').FormulaU='RGB(248,250,252)'; sh.CellsU('LinePattern').FormulaU='0'
        except Exception: pass
    use.Close(); cls.Close()

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--page',required=True); ap.add_argument('--output',default=os.path.join(VISIO_DIR,'CityNexus_Visio_Model_Baseline_v1.0.3_RC4.vsdx')); args=ap.parse_args()
    app=win32com.client.Dispatch('Visio.Application'); app.Visible=False
    if os.path.exists(args.output): doc=app.Documents.Open(args.output)
    else: doc=app.Documents.Add(TEMPLATE)
    if doc.Pages.Count==1 and doc.Pages.Item(1).NameU in ('Page-1','Page1'):
        page=doc.Pages.Item(1)
    else:
        page=doc.Pages.Add()
    render(os.path.join(SPEC,args.page+'.yaml'),doc,app,page); doc.SaveAs(args.output); doc.Close(); app.Quit()
if __name__=='__main__': main()
