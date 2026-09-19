"""Apply style-token values to native rendering subshapes recursively."""
def apply_style(shape, token, colors, font_id):
    cfg=token or {}; fill=colors.get(cfg.get('fill','surface'),cfg.get('fill')); stroke=colors.get(cfg.get('stroke','line'),cfg.get('stroke')); text=colors.get(cfg.get('text','text'),cfg.get('text'))
    def walk(s):
        for cell,val in [('FillForegnd',fill),('LineColor',stroke),('Char.Color',text)]:
            if val:
                try:s.CellsU(cell).FormulaU='RGB(%d,%d,%d)'%tuple(int(val.lstrip('#')[i:i+2],16) for i in (0,2,4)) if str(val).startswith('#') else str(val)
                except:pass
        try:s.CellsU('Char.Font').FormulaU=str(font_id)
        except:pass
        try: walk(s.Shapes)
        except: pass
    if hasattr(shape,'__iter__'):
        for s in shape: walk(s)
    else: walk(shape)
