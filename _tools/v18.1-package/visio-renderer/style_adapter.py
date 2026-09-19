"""Strict styleRef adapter for native Visio UML shapes."""
class RendererError(RuntimeError):
    pass
def rgb_formula(value):
    h=value.lstrip('#'); return 'RGB(%d,%d,%d)'%tuple(int(h[i:i+2],16) for i in (0,2,4))
def _force(shape,cell,formula,required=True,warnings=None):
    try:
        if not shape.CellExistsU(cell,0):
            if required: raise RendererError(f'{shape.NameU}: missing {cell}')
            if warnings is not None: warnings.append(f'{shape.NameU}: optional {cell} unavailable')
            return
        c=shape.CellsU(cell)
        try: c.FormulaForceU=formula
        except Exception: c.FormulaU=formula
    except RendererError: raise
    except Exception as e:
        if required: raise RendererError(f'{shape.NameU}: cannot set {cell}: {e}') from e
        if warnings is not None: warnings.append(f'{shape.NameU}: optional {cell}: {e}')
def walk(shape):
    """Traverse a COM Shape and every nested child Shape."""
    yield shape
    try:
        children = shape.Shapes
        count = int(children.Count)
    except Exception:
        count = 0
        children = None
    if children is not None:
        for i in range(1, count + 1):
            yield from walk(children.Item(i))


def _has_text(shape):
    try:
        return bool(str(shape.Text).strip())
    except Exception:
        try:
            return bool(str(shape.CellsU('TheText').FormulaU).strip())
        except Exception:
            return False
def resolve_style(ref,tokens):
    try: raw=tokens['shapeStyles'][ref]
    except KeyError as e: raise RendererError(f'undefined styleRef {ref}') from e
    colors=tokens['colors']; cv=lambda k,d: colors.get(raw.get(k,d),raw.get(k,d))
    return {'fill':cv('fill','surface'),'stroke':cv('stroke','line'),'text':cv('text','text'),'width':raw.get('strokeWidthPt',1.0),'dash':raw.get('dash','solid')}
def apply_style(shape,spec_id,ref,tokens,font_id,warnings):
    s=resolve_style(ref,tokens)
    for index, node in enumerate(walk(shape)):
        # The root owns the semantic style. Child shapes are formatted when
        # they expose a real rendering cell; text-bearing children always get
        # the calibrated font and text colour.
        cells = [
            ('FillForegnd', rgb_formula(s['fill']), index == 0),
            ('FillBkgnd', rgb_formula(s['fill']), False),
            ('FillPattern', '1', index == 0),
            ('LineColor', rgb_formula(s['stroke']), index == 0),
            ('LineWeight', f'{s["width"]} pt', index == 0),
            ('LinePattern', '1' if s['dash'] == 'solid' else '2', index == 0),
            ('ShdwPattern', '0', False),
            ('GlowSize', '0', False),
        ]
        if index == 0 or _has_text(node):
            cells.extend([
                ('Char.Font', str(font_id), True),
                ('Char.Color', rgb_formula(s['text']), True),
            ])
        for cell, val, required in cells:
            _force(node, cell, val, required, warnings)
    return s
