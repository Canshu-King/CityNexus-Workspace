"""Presentation-layer helpers for CityNexus Visio renderer.

Coordinates use the CityNexus convention:
- units: cm
- logical origin: top-left
- x/y: shape centre

The helpers intentionally keep presentation shapes separate from semantic UML
shapes by assigning Prop.Role = presentation.
"""
from __future__ import annotations


MM_PER_IN = 25.4
CM_PER_IN = 2.54


def cm_to_in(value: float) -> float:
    return float(value) / CM_PER_IN


def logical_center_to_visio(x_cm: float, y_cm: float, page_h_cm: float) -> tuple[float, float]:
    return cm_to_in(x_cm), cm_to_in(page_h_cm - y_cm)


def rect_from_center(x_cm: float, y_cm: float, w_cm: float, h_cm: float, page_h_cm: float):
    x, y = logical_center_to_visio(x_cm, y_cm, page_h_cm)
    w, h = cm_to_in(w_cm), cm_to_in(h_cm)
    return x - w / 2, y - h / 2, x + w / 2, y + h / 2


def effective_bounds(shape) -> dict[str, float]:
    """Return effective Visio bounds without assuming LocPin is the centre."""
    pin_x = float(shape.CellsU("PinX").Result("inches"))
    pin_y = float(shape.CellsU("PinY").Result("inches"))
    loc_x = float(shape.CellsU("LocPinX").Result("inches"))
    loc_y = float(shape.CellsU("LocPinY").Result("inches"))
    width = float(shape.CellsU("Width").Result("inches"))
    height = float(shape.CellsU("Height").Result("inches"))
    left = pin_x - loc_x
    bottom = pin_y - loc_y
    return {
        "left": left,
        "bottom": bottom,
        "right": left + width,
        "top": bottom + height,
        "centerX": left + width / 2,
        "centerY": bottom + height / 2,
        "width": width,
        "height": height,
    }


def _force(cell, formula: str) -> None:
    try:
        cell.FormulaForceU = formula
    except Exception:
        cell.FormulaU = formula


def _rgb(hex_value: str) -> str:
    h = hex_value.lstrip("#")
    if len(h) != 6:
        raise ValueError(f"invalid colour: {hex_value}")
    r, g, b = (int(h[i:i+2], 16) for i in (0, 2, 4))
    return f"RGB({r},{g},{b})"


def set_geometry_from_center(shape, *, x_cm: float, y_cm: float, w_cm: float, h_cm: float, page_h_cm: float) -> None:
    """Set a shape's final geometry using the shared centre-based convention."""
    x_in, y_in = logical_center_to_visio(x_cm, y_cm, page_h_cm)
    _force(shape.CellsU("PinX"), f"{x_in} in")
    _force(shape.CellsU("PinY"), f"{y_in} in")
    _force(shape.CellsU("Width"), f"{cm_to_in(w_cm)} in")
    _force(shape.CellsU("Height"), f"{cm_to_in(h_cm)} in")


def style_text(shape, *, font_id: int, color: str, size_pt: float, horizontal: str = "left", vertical: str = "middle") -> None:
    _force(shape.CellsU("Char.Font"), str(int(font_id)))
    _force(shape.CellsU("Char.Color"), _rgb(color))
    _force(shape.CellsU("Char.Size"), f"{float(size_pt)} pt")
    if shape.CellExistsU("Para.HorzAlign", 0):
        mapping = {"left": 0, "center": 1, "right": 2}
        _force(shape.CellsU("Para.HorzAlign"), str(mapping[horizontal]))
    if shape.CellExistsU("VerticalAlign", 0):
        mapping = {"top": 0, "middle": 1, "bottom": 2}
        _force(shape.CellsU("VerticalAlign"), str(mapping[vertical]))


def style_presentation_box(shape, *, fill: str | None, stroke: str | None, line_weight_pt: float = 0.8) -> None:
    if fill is None:
        _force(shape.CellsU("FillPattern"), "0")
    else:
        _force(shape.CellsU("FillPattern"), "1")
        _force(shape.CellsU("FillForegnd"), _rgb(fill))
    if stroke is None:
        _force(shape.CellsU("LinePattern"), "0")
    else:
        _force(shape.CellsU("LinePattern"), "1")
        _force(shape.CellsU("LineColor"), _rgb(stroke))
        _force(shape.CellsU("LineWeight"), f"{float(line_weight_pt)} pt")
    if shape.CellExistsU("ShdwPattern", 0):
        _force(shape.CellsU("ShdwPattern"), "0")
    if shape.CellExistsU("GlowSize", 0):
        _force(shape.CellsU("GlowSize"), "0")
