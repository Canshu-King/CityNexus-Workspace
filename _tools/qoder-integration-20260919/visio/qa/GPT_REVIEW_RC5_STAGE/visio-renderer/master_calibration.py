"""Discover localized native UML masters and their child ShapeSheet structure."""
import json, os, win32com.client
ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),'..'))
CONTENT=os.path.join(os.environ.get('ProgramFiles','C:/Program Files'),'Microsoft Office','root','Office16','Visio Content','2052')
STENCILS={'uml':os.path.join(CONTENT,'UUSEME_M.VSSX'),'class':os.path.join(CONTENT,'USTRME_M.VSSX')}
NAMES={'Actor':'uml','Use Case':'uml','Subsystem':'uml','Association':'uml','Dependency':'class','Composition':'class','Extend':'uml','Class':'class','Member':'class'}
def cells(s):
    out=[]
    for n in ('PinX','PinY','Width','Height','Char.Font','Char.Color','FillForegnd','LineColor','LineWeight','LinePattern'):
        try: out.append({'cell':n,'formula':s.CellsU(n).FormulaU})
        except: pass
    return out
def tree(s):
    return {'name':s.NameU,'id':getattr(s,'ID',None),'cells':cells(s),'children':[tree(x) for x in s.Shapes]}
def main():
    app=win32com.client.Dispatch('Visio.Application'); app.Visible=False; result={'stencils':{},'generatedBy':'local Visio COM'}
    opened=[]; host=None
    try:
      host=app.Documents.Add(''); page=host.Pages.Item(1)
      for name,which in NAMES.items():
        d=app.Documents.OpenEx(STENCILS[which],66); opened.append(d); m=d.Masters.ItemU(name)
        sh=page.Drop(m,2,2)
        result['stencils'][name]={'stencil':STENCILS[which],'masterID':m.ID,'masterNameU':m.NameU,'instance':tree(sh)}
      out=os.path.join(os.path.dirname(__file__),'native-master-map.json'); json.dump(result,open(out,'w',encoding='utf-8'),ensure_ascii=False,indent=2)
      print(out)
    finally:
      for d in opened:
        try:d.Close()
        except:pass
      try: host.Close()
      except: pass
      app.Quit()
if __name__=='__main__': main()
