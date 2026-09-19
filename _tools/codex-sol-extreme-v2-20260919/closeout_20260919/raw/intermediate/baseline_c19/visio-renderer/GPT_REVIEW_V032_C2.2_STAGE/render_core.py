"""Native Visio primitives shared by production and calibration builders."""
from style_adapter import RendererError
def set_prop(shape,name,value):
    try:
        if not shape.CellExistsU('Prop.'+name,0): shape.AddNamedRow(243,name,0)
        shape.CellsU('Prop.'+name).FormulaU='"'+str(value).replace('"','""')+'"'
    except Exception as e: raise RendererError(f'cannot set Prop.{name}: {e}') from e
def resolve_font_id(doc,name='Segoe UI'):
    for i in range(1,doc.Fonts.Count+1):
        if str(doc.Fonts.Item(i).Name).strip().lower()==name.lower(): return i
    raise RendererError(f'font not found: {name}')


def load_master_map(path):
    import json
    with open(path, encoding='utf8') as handle:
        return json.load(handle)
