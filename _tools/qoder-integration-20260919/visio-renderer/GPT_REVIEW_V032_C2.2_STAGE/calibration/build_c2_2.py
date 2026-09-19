"""Build the C2.2 native Class anchoring calibration.

This calibration is deliberately independent from the historical C2.1 builder.  The
Class master in the installed UML stencil uses a bottom-left logical origin
(LocPinX/LocPinY = 0), therefore overlays are formula-linked to the owner's
effective bounds rather than to a presumed centre pin.
"""
from __future__ import annotations

import json
import os
import sys
from typing import Iterable

import win32com.client
import yaml

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from render_core import load_master_map, resolve_font_id, set_prop  # noqa: E402
from style_adapter import apply_style  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
HERE = os.path.dirname(__file__)
OUT = os.path.join(HERE, "out")
os.makedirs(OUT, exist_ok=True)


def force(cell, formula: str) -> None:
    try:
        cell.FormulaForceU = formula
    except Exception:
        cell.FormulaU = formula


def all_shapes(root) -> Iterable:
    """Yield a root Shape and all descendants (or a Shapes collection)."""
    try:
        count = int(root.Count)
        for i in range(1, count + 1):
            shape = root.Item(i)
            yield shape
            try:
                yield from all_shapes(shape)
            except Exception:
                pass
        return
    except Exception:
        pass
    shape = root
    yield shape
    try:
        yield from all_shapes(shape.Shapes)
    except Exception:
        pass


def effective_bounds(shape):
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


def set_formula(shape, cell_name: str, formula: str) -> None:
    if not shape.CellExistsU(cell_name, 0):
        raise RuntimeError(f"{shape.NameU}: missing {cell_name}")
    force(shape.CellsU(cell_name), formula)


def text_of(shape) -> str:
    try:
        return str(shape.Text)
    except Exception:
        return ""


def hide_empty_defaults(page) -> None:
    """Hide only empty top-level list rows, retaining the native class body."""
    for i in range(int(page.Shapes.Count), 0, -1):
        shape = page.Shapes.Item(i)
        name = str(shape.NameU)
        if name == "Member" or name.startswith("Member.") or name == "Separator" or name.startswith("Separator."):
            # These are the master's empty list rows; deleting them does not
            # touch Sheet.31 (the native Class body/header separator).
            try:
                shape.Text = ""
                shape.Delete()
            except Exception:
                if shape.CellExistsU("LinePattern", 0):
                    force(shape.CellsU("LinePattern"), "0")
                if shape.CellExistsU("FillPattern", 0):
                    force(shape.CellsU("FillPattern"), "0")


def set_native_stereotype(owner, label: str) -> bool:
    """Use the Class master's own stereotype child; never add a fake overlay."""
    found = False
    for node in all_shapes(owner):
        try:
            if node.CellExistsU("User.StereoType", 0):
                force(node.CellsU("User.StereoType"), "TRUE")
            txt = text_of(node)
            if "构造型" in txt or "stereotype" in str(node.NameU).lower():
                node.Text = label
                found = True
        except Exception:
            continue
    try:
        force(owner.CellsU("User.StereoType"), "TRUE")
    except Exception:
        pass
    return found


def overlay_formula(owner_id: int, order: int, top_margin: float, field_h: float, row_gap: float):
    p = f"Sheet.{owner_id}!"
    x = f"{p}PinX-{p}LocPinX+{p}Width*0.5"
    width = f"{p}Width-0.16 in"
    body_top = f"{p}PinY-{p}LocPinY+{p}Height-{p}User.HdrHgt"
    y = f"{body_top}-{top_margin} in-{field_h} in*0.5-{order - 1}*({field_h} in+{row_gap} in)"
    return x, y, width


def main() -> int:
    tokens = yaml.safe_load(open(os.path.join(ROOT, "visio-spec", "style-tokens.yaml"), encoding="utf-8"))
    master_map = load_master_map(os.path.join(ROOT, "visio-renderer", "native-master-map.json"))
    app = win32com.client.Dispatch("Visio.Application")
    app.Visible = False
    app.AlertResponse = 7
    doc = app.Documents.Add("")
    page = doc.Pages.Item(1)
    page.NameU = "C2_Anchored_Class_v3"
    font_id = resolve_font_id(doc, "Segoe UI")
    stencil_path = master_map["stencils"]["Class"]["stencil"]
    stencil = app.Documents.OpenEx(stencil_path, 66)
    master = stencil.Masters.ItemU("Class")
    owners = []
    fields_meta = []
    anchor_tests = []
    resize_tests = []
    try:
        specs = [
            ("C2-JOURNEY", "classJourney", "Journey", ["journeyId", "lifecycleState", "healthStatus"], 3.0),
            ("C2-JOURNEY-TWIN", "classProjection", "JourneyTwin", ["healthStatus", "riskScore"], 5.5),
        ]
        for spec_id, style_ref, title, fields, x in specs:
            owner = page.Drop(master, x, 4.0)
            owner.Text = title
            set_prop(owner, "SpecId", spec_id)
            set_prop(owner, "StyleRef", style_ref)
            apply_style(owner, spec_id, style_ref, tokens, font_id, [])
            stereo_label = "<<aggregate root>>" if title == "Journey" else "<<projection>>"
            set_native_stereotype(owner, stereo_label)

            # Read the effective native header after text/stereotype, then reserve body rows.
            header_h = float(owner.CellsU("User.HdrHgt").Result("inches"))
            top_margin = 1.5 / 25.4
            bottom_margin = 1.5 / 25.4
            field_h = 4.6 / 25.4
            row_gap = 1.0 / 25.4
            required_body = top_margin + bottom_margin + len(fields) * field_h + max(0, len(fields) - 1) * row_gap
            required_height = header_h + required_body
            current_height = float(owner.CellsU("Height").Result("inches"))
            if current_height < required_height:
                set_formula(owner, "Height", f"{required_height} in")

            owners.append({"specId": spec_id, "shape": owner, "fields": fields, "headerHeight": header_h})
            for order, field_name in enumerate(fields, 1):
                overlay = page.DrawRectangle(x, 0.0, x + 0.01, 0.01)
                overlay.Text = field_name
                field_id = f"{spec_id}-FIELD-{order}"
                set_prop(overlay, "SpecId", field_id)
                set_prop(overlay, "Role", "presentation")
                set_prop(overlay, "OwnerSpecId", spec_id)
                set_prop(overlay, "ContentRole", "field")
                set_prop(overlay, "FieldOrder", order)
                x_formula, y_formula, width_formula = overlay_formula(owner.ID, order, top_margin, field_h, row_gap)
                set_formula(overlay, "PinX", x_formula)
                set_formula(overlay, "PinY", y_formula)
                set_formula(overlay, "Width", width_formula)
                set_formula(overlay, "Height", f"{field_h} in")
                set_formula(overlay, "FillPattern", "0")
                set_formula(overlay, "LinePattern", "0")
                set_formula(overlay, "ShdwPattern", "0")
                set_formula(overlay, "Char.Font", str(font_id))
                set_formula(overlay, "Char.Color", "RGB(15,23,42)")
                fields_meta.append({
                    "specId": field_id, "ownerSpecId": spec_id, "fieldOrder": order,
                    "ownerShapeId": int(owner.ID), "shape": overlay,
                    "xFormula": x_formula, "yFormula": y_formula, "widthFormula": width_formula,
                })

        hide_empty_defaults(page)

        # Move test: all formula-linked overlays must follow the owner's effective position.
        for field in fields_meta:
            owner = next(x["shape"] for x in owners if x["specId"] == field["ownerSpecId"])
            overlay = field["shape"]
            before_o = effective_bounds(owner)
            before_f = effective_bounds(overlay)
            original_pin_x = float(owner.CellsU("PinX").Result("inches"))
            original_pin_y = float(owner.CellsU("PinY").Result("inches"))
            force(owner.CellsU("PinX"), f"{original_pin_x + 20 / 25.4} in")
            force(owner.CellsU("PinY"), f"{original_pin_y + 10 / 25.4} in")
            after_f = effective_bounds(overlay)
            err = max(
                abs((after_f["centerX"] - before_f["centerX"]) - 20 / 25.4),
                abs((after_f["centerY"] - before_f["centerY"]) - 10 / 25.4),
            ) * 25.4
            anchor_tests.append({"field": field["specId"], "owner": field["ownerSpecId"], "deltaErrorMm": err})
            force(owner.CellsU("PinX"), f"{original_pin_x} in")
            force(owner.CellsU("PinY"), f"{original_pin_y} in")

        # Resize test: width follows effective owner width and fields remain in body.
        for owner_rec in owners:
            owner = owner_rec["shape"]
            before_o = effective_bounds(owner)
            old_w, old_h = before_o["width"], before_o["height"]
            force(owner.CellsU("Width"), f"{old_w + 10 / 25.4} in")
            force(owner.CellsU("Height"), f"{old_h + 8 / 25.4} in")
            after_o = effective_bounds(owner)
            owner_fields = [f for f in fields_meta if f["ownerSpecId"] == owner_rec["specId"]]
            measurements = []
            for field in owner_fields:
                fb = effective_bounds(field["shape"])
                measurements.append({
                    "field": field["specId"],
                    "centerXErrorMm": abs(fb["centerX"] - after_o["centerX"]) * 25.4,
                    "width": fb["width"],
                    "insideBody": fb["bottom"] >= after_o["bottom"] + 1.5 / 25.4 and fb["top"] <= after_o["top"] - float(owner.CellsU("User.HdrHgt").Result("inches")) - 1.5 / 25.4,
                })
            resize_tests.append({"owner": owner_rec["specId"], "fields": measurements})
            force(owner.CellsU("Width"), f"{old_w} in")
            force(owner.CellsU("Height"), f"{old_h} in")

        out_vsdx = os.path.join(OUT, "C2_Anchored_Class_v3.vsdx")
        out_svg = os.path.join(OUT, "C2_Anchored_Class_v3.raw.svg")
        out_png = os.path.join(OUT, "C2_Anchored_Class_v3.png")
        doc.SaveAs(out_vsdx)
        page.Export(out_svg)
        page.Export(out_png)
        report = {
            "calibration": "C2.2",
            "artifact": "C2_Anchored_Class_v3",
            "font": {"name": "Segoe UI", "fontId": int(font_id)},
            "nativeClassMaster": "Class",
            "stereotypeMode": "native User.StereoType + native child text",
            "fieldOverlayCount": len(fields_meta),
            "anchorBehaviour": "PASS" if max((x["deltaErrorMm"] for x in anchor_tests), default=0) <= 0.5 else "FAIL",
            "resizeAnchorBehaviour": "PASS" if all(m["insideBody"] and m["centerXErrorMm"] <= 0.5 for r in resize_tests for m in r["fields"]) else "FAIL",
            "anchorTests": anchor_tests,
            "resizeTests": resize_tests,
            "status": "BUILT",
        }
        with open(os.path.join(OUT, "C2_Anchored_Class_v3-report.json"), "w", encoding="utf-8") as handle:
            json.dump(report, handle, ensure_ascii=False, indent=2)
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0
    finally:
        try:
            stencil.Close()
        except Exception:
            pass
        try:
            doc.Close()
        except Exception:
            pass
        app.Quit()


if __name__ == "__main__":
    raise SystemExit(main())
