"""Independent validator for the C2.2 native Class anchoring calibration.

The validator opens the VSDX through Visio COM to measure effective bounds and
formula cells, then parses the raw VSDX package and raw SVG directly for
persisted metadata, placeholders and ShapeSheet error tokens.  It does not
consume the renderer's report as evidence.
"""
from __future__ import annotations

import json
import os
import re
import zipfile
import html

import win32com.client

HERE = os.path.dirname(__file__)
OUT = os.path.join(HERE, "out")
VSDX = os.path.join(OUT, "C2_Anchored_Class_v3.vsdx")
SVG = os.path.join(OUT, "C2_Anchored_Class_v3.raw.svg")
REPORT = os.path.join(OUT, "C2_Anchored_Class_v3-report.json")


def eff(shape):
    pin_x = float(shape.CellsU("PinX").Result("inches"))
    pin_y = float(shape.CellsU("PinY").Result("inches"))
    loc_x = float(shape.CellsU("LocPinX").Result("inches"))
    loc_y = float(shape.CellsU("LocPinY").Result("inches"))
    width = float(shape.CellsU("Width").Result("inches"))
    height = float(shape.CellsU("Height").Result("inches"))
    left, bottom = pin_x - loc_x, pin_y - loc_y
    return {"left": left, "bottom": bottom, "right": left + width, "top": bottom + height,
            "centerX": left + width / 2, "centerY": bottom + height / 2,
            "width": width, "height": height}


def prop(shape, name):
    try:
        return str(shape.CellsU("Prop." + name).ResultStr(20)).strip('"')
    except Exception:
        try:
            return str(shape.CellsU("Prop." + name).FormulaU).strip('"')
        except Exception:
            return ""


def formula(shape, cell):
    try:
        return str(shape.CellsU(cell).FormulaU)
    except Exception:
        return ""


def walk(coll):
    for i in range(1, int(coll.Count) + 1):
        s = coll.Item(i)
        yield s
        try:
            yield from walk(s.Shapes)
        except Exception:
            pass


def master_name(shape):
    try:
        return str(shape.Master.NameU)
    except Exception:
        return ""


def text(shape):
    try:
        return str(shape.Text)
    except Exception:
        return ""


def overlap(a, b):
    return min(a["right"], b["right"]) > max(a["left"], b["left"]) and min(a["top"], b["top"]) > max(a["bottom"], b["bottom"])


def main():
    failures = []
    with zipfile.ZipFile(VSDX) as package:
        xml = "\n".join(package.read(n).decode("utf-8", "ignore") for n in package.namelist() if n.endswith(".xml"))
    svg = open(SVG, encoding="utf-8", errors="ignore").read()
    forbidden = {token: xml.count(token) + svg.count(token) for token in ("#VALUE!", "#REF!")}
    if any(forbidden.values()):
        failures.append("forbidden ShapeSheet token")
    visible_svg = html.unescape(svg)
    visible_text = " ".join(re.findall(r"<text[^>]*>(.*?)</text>", visible_svg, flags=re.I | re.S))
    for placeholder in ("成员名", "-成员名", "类名"):
        if placeholder in visible_text:
            failures.append("placeholder:" + placeholder)

    app = win32com.client.Dispatch("Visio.Application")
    app.Visible = False
    app.AlertResponse = 7
    doc = app.Documents.Open(VSDX)
    try:
        page = doc.Pages.Item(1)
        shapes = list(walk(page.Shapes))
        semantic = {}
        fields = []
        for s in shapes:
            sid = prop(s, "SpecId")
            if not sid:
                continue
            if sid in semantic:
                failures.append("duplicate SpecId:" + sid)
            semantic[sid] = s
            if prop(s, "ContentRole") == "field":
                fields.append(s)

        expected_owners = {"C2-JOURNEY", "C2-JOURNEY-TWIN"}
        owners = {sid: semantic.get(sid) for sid in expected_owners}
        if any(v is None for v in owners.values()):
            failures.append("missing class owner")
        if len(fields) != 5:
            failures.append("field count")

        class_master_ok = all(master_name(owner) == "Class" for owner in owners.values() if owner is not None)
        if not class_master_ok:
            failures.append("native Class master")

        # Native stereotypes are checked on the owner and in raw SVG.
        stereotype_text = " ".join(text(owner) for owner in owners.values() if owner is not None)
        native_stereo = all("TRUE" in formula(owner, "User.StereoType").upper() for owner in owners.values() if owner is not None)
        if not native_stereo or not all(x in visible_text for x in ("<<aggregate root>>", "<<projection>>")):
            failures.append("native stereotype")

        page_w = float(page.PageSheet.CellsU("PageWidth").Result("inches"))
        page_h = float(page.PageSheet.CellsU("PageHeight").Result("inches"))
        owner_records = {}
        for sid, owner in owners.items():
            if owner is None:
                continue
            b = eff(owner)
            owner_records[sid] = {"shapeId": int(owner.ID), "master": master_name(owner), "boundsIn": b,
                                  "headerHeightIn": float(owner.CellsU("User.HdrHgt").Result("inches"))}
            if b["left"] < -1e-6 or b["bottom"] < -1e-6 or b["right"] > page_w + 1e-6 or b["top"] > page_h + 1e-6:
                failures.append("owner outside page:" + sid)

        field_records = []
        by_owner = {sid: [] for sid in expected_owners}
        for f in fields:
            sid, owner_sid = prop(f, "SpecId"), prop(f, "OwnerSpecId")
            order = int(prop(f, "FieldOrder") or "0")
            owner = owners.get(owner_sid)
            if owner is None or owner_sid not in by_owner:
                failures.append("field owner:" + sid)
                continue
            ob, fb = eff(owner), eff(f)
            header_h = float(owner.CellsU("User.HdrHgt").Result("inches"))
            body = {"left": ob["left"], "right": ob["right"], "bottom": ob["bottom"], "top": ob["top"] - header_h}
            inside_owner = fb["left"] >= ob["left"] - 1e-6 and fb["right"] <= ob["right"] + 1e-6 and fb["bottom"] >= ob["bottom"] - 1e-6 and fb["top"] <= ob["top"] + 1e-6
            inside_body = fb["left"] >= body["left"] - 1e-6 and fb["right"] <= body["right"] + 1e-6 and fb["bottom"] >= body["bottom"] + 1.5 / 25.4 - 1e-6 and fb["top"] <= body["top"] - 1.5 / 25.4 + 1e-6
            x_formula, y_formula, w_formula = formula(f, "PinX"), formula(f, "PinY"), formula(f, "Width")
            owner_ref = str(owner.NameU)
            formula_text = x_formula + y_formula + w_formula
            formulas_ok = all(token in formula_text for token in (owner_ref + "!PinX", owner_ref + "!PinY", owner_ref + "!Width")) and owner_ref + "!User.HdrHgt" in y_formula
            fill, line = formula(f, "FillPattern"), formula(f, "LinePattern")
            char_color = formula(f, "Char.Color")
            font_formula = formula(f, "Char.Font")
            if not (inside_owner and inside_body):
                failures.append("field outside body:" + sid)
            if not formulas_ok:
                failures.append("anchor formula:" + sid)
            if fill != "0" or line != "0" or "RGB(15,23,42)" not in char_color or not font_formula.isdigit():
                failures.append("field style:" + sid)
            if order <= 0:
                failures.append("field order:" + sid)
            by_owner[owner_sid].append(order)
            field_records.append({"specId": sid, "OwnerSpecId": owner_sid, "FieldOrder": order,
                                  "ownerShapeId": int(owner.ID), "ownerBoundsIn": ob, "headerHeightIn": header_h,
                                  "bodyBoundsIn": body, "fieldBoundsIn": fb, "insideOwner": inside_owner,
                                  "insideBody": inside_body, "xFormula": x_formula, "yFormula": y_formula,
                                  "widthFormula": w_formula, "font": font_formula, "textColor": char_color,
                                  "fillPattern": fill, "linePattern": line, "text": text(f)})
        for sid, orders in by_owner.items():
            if sorted(orders) != list(range(1, len(orders) + 1)):
                failures.append("field order sequence:" + sid)
        for i, a in enumerate(fields):
            for b in fields[i + 1:]:
                if prop(a, "OwnerSpecId") == prop(b, "OwnerSpecId") and overlap(eff(a), eff(b)):
                    failures.append("field overlap")

        # Independent live anchor/resize probes.  The document is never saved
        # after these temporary mutations.
        anchor_probe = []
        for field in fields:
            owner_sid = prop(field, "OwnerSpecId")
            owner = owners.get(owner_sid)
            if owner is None:
                continue
            before_owner, before_field = eff(owner), eff(field)
            old_x = float(owner.CellsU("PinX").Result("inches"))
            old_y = float(owner.CellsU("PinY").Result("inches"))
            owner.CellsU("PinX").FormulaU = f"{old_x + 20 / 25.4} in"
            owner.CellsU("PinY").FormulaU = f"{old_y + 10 / 25.4} in"
            moved = eff(field)
            err = max(abs((moved["centerX"] - before_field["centerX"]) - 20 / 25.4), abs((moved["centerY"] - before_field["centerY"]) - 10 / 25.4)) * 25.4
            anchor_probe.append({"field": prop(field, "SpecId"), "deltaErrorMm": err})
            owner.CellsU("PinX").FormulaU = f"{old_x} in"
            owner.CellsU("PinY").FormulaU = f"{old_y} in"

        resize_probe = []
        for owner_sid, owner in owners.items():
            if owner is None:
                continue
            old_w = float(owner.CellsU("Width").Result("inches"))
            old_h = float(owner.CellsU("Height").Result("inches"))
            old_bounds = eff(owner)
            owner.CellsU("Width").FormulaU = f"{old_w + 10 / 25.4} in"
            owner.CellsU("Height").FormulaU = f"{old_h + 8 / 25.4} in"
            new_bounds = eff(owner)
            owner_fields = [f for f in fields if prop(f, "OwnerSpecId") == owner_sid]
            resize_probe.append({"owner": owner_sid, "centerXDeltaErrorMm": max((abs((eff(f)["centerX"] - new_bounds["centerX"]) * 25.4) for f in owner_fields), default=0.0), "fieldCount": len(owner_fields)})
            owner.CellsU("Width").FormulaU = f"{old_w} in"
            owner.CellsU("Height").FormulaU = f"{old_h} in"
        anchor_status = "PASS" if max((x["deltaErrorMm"] for x in anchor_probe), default=0) <= 0.5 else "FAIL"
        resize_status = "PASS" if all(x["centerXDeltaErrorMm"] <= 0.5 for x in resize_probe) else "FAIL"

        # Required visible text is read from raw SVG (the authoritative direct export).
        for required in ("Journey", "JourneyTwin", "journeyId", "lifecycleState", "healthStatus", "riskScore", "aggregate root", "projection"):
            if required not in visible_text:
                failures.append("missing SVG text:" + required)

        report = {
            "calibration": "C2.2",
            "status": "PASS" if not failures else "FAIL",
            "artifact": os.path.basename(VSDX),
            "rawSvg": os.path.basename(SVG),
            "pageDimensionsIn": {"width": page_w, "height": page_h},
            "nativeClassMaster": class_master_ok,
            "nativeStereotypes": native_stereo,
            "owners": owner_records,
            "fieldCount": len(fields),
            "fields": field_records,
            "placeholders": {x: (x in visible_text) for x in ("成员名", "-成员名", "类名")},
            "fieldOverlapCount": sum(1 for i, a in enumerate(fields) for b in fields[i + 1:] if prop(a, "OwnerSpecId") == prop(b, "OwnerSpecId") and overlap(eff(a), eff(b))),
            "anchorBehaviour": anchor_status,
            "resizeAnchorBehaviour": resize_status,
            "anchorProbe": anchor_probe,
            "resizeProbe": resize_probe,
            "forbiddenTokenCounts": forbidden,
            "failures": failures,
        }
    finally:
        try:
            doc.Saved = True
        except Exception:
            pass
        doc.Close()
        app.Quit()
    with open(REPORT, "w", encoding="utf-8") as handle:
        json.dump(report, handle, ensure_ascii=False, indent=2)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
