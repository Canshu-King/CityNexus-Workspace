"""Native UML Class adapter; avoids placeholder member text."""
def apply_class(shape, spec, font_id):
    shape.Text=spec.get('text','')
    try:
        shape.CellsU('User.HideOperations').FormulaU='TRUE'
    except: pass
    # Native class groups expose member rows as children; set visible text explicitly.
    fields=spec.get('fields',[]); text=spec.get('text','')
    if spec.get('stereotype'): text=spec['stereotype']+'\n'+text
    if fields: text+='\n'+'\n'.join(str(x) for x in fields)
    shape.Text=text
    try: shape.CellsU('Char.Font').FormulaU=str(font_id)
    except: pass
