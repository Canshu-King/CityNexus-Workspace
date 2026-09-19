"""Hardened independent validator for the frozen C2.2 Class calibration.

This version keeps the effective-bounds model that fixed LocPin handling and
adds checks that were missing from the original review package:
- correct owner-specific native stereotype text
- visible SVG font family
- exact field set/order per owner
- resized field width/body/order/overlap behaviour
- no visible default Member/Separator artifacts
"""
from __future__ import annotations

import html
import json
import os
import re
import zipfile

import win32com.client

HERE = os.path.dirname(__file__)
OUT = os.path.join(HERE, "out")
VSDX = os.path.join(OUT, "C2_Anchored_Class_v3.vsdx")
SVG = os.path.join(OUT, "C2_Anchored_Class_v3.raw.svg")
REPORT = os.path.join(OUT, "C2_Anchored_Class_v3-report.json")
TOL_MM = 0.5
TOL_IN = TOL_MM / 25.4
BODY_MARGIN_IN = 1.5 / 25.4
EXPECTED = {
    "C2-JOURNEY": {
        "stereotype": "<<aggregate root>>",
        "fields": ["journeyId", "lifecycleState", "healthStatus"],
    },
    "C2-JOURNEY-TWIN": {
        "stereotype": "<<projection>>",
        "fields": ["healthStatus", "riskScore"],
    },
}


def eff(shape):
    pin_x = float(shape.CellsU("PinX").Result("inches"))
    pin_y = float(shape.CellsU("PinY").Result("inches"))
    loc_x = float(shape.CellsU("LocPinX").Result("inches"))
    loc_y = float(shape.CellsU("LocPinY").Result("inches"))
    width = float(shape.CellsU("Width").Result("inches"))
    height = float(shape.CellsU("Height").Result("inches"))
    left, bottom = pin_x - loc_x, pin_y - loc_y
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


def subtree_text(shape) -> str:
    values = []
    try:
        values.append(text(shape))
        values.extend(text(s) for s in walk(shape.Shapes))
    except Exception:
        pass
    return " ".join(x for x in values if x)


def overlap(a, b):
    return min(a["right"], b["right"]) > max(a["left"], b["left"]) and min(a["top"], b["top"]) > max(a["bottom"], b["bottom"])


def visible_svg_text_and_fonts(svg: str):
    css = {m.group(1): m.group(2) for m in re.finditer(r"\.(st\d+)\s*\{([^}]*)\}", svg, re.I | re.S)}
    records = []
    for tm in re.finditer(r'<text([^>]*)>(.*?)</text>', svg, re.I | re.S):
        attrs = tm.group(1)
        raw = re.sub(r"<[^>]+>", "", tm.group(2))
        value = html.unescape(raw).strip()
        cls_m = re.search(r'class="([^"]+)"', attrs)
        cls = cls_m.group(1).split()[0] if cls_m else ""
        style = css.get(cls, "")
        fam_m = re.search(r"font-family:([^;}]+)", style, re.I)
        family = fam_m.group(1).strip() if fam_m else ""
        records.append({"text": value, "font": family, "class": cls})
    return records


def body_bounds(owner):
    ob = eff(owner)
    header_h = float(owner.CellsU("User.HdrHgt").Result("inches"))
    return ob, header_h, {
        "left": ob["left"],
        "right": ob["right"],
        "bottom": ob["bottom"],
        "top": ob["top"] - header_h,
    }


def inside_body(field_bounds, body):
    return (
        field_bounds["left"] >= body["left"] - 1e-6
        and field_bounds["right"] <= body["right"] + 1e-6
        and field_bounds["bottom"] >= body["bottom"] + BODY_MARGIN_IN - 1e-6
        and field_bounds["top"] <= body["top"] - BODY_MARGIN_IN + 1e-6
    )


def main():
    failures = []
    with zipfile.ZipFile(VSDX) as package:
        xml = "\n".join(package.read(n).decode("utf-8", "ignore") for n in package.namelist() if n.endswith(".xml"))
    svg = open(SVG, encoding="utf-8", errors="ignore").read()
    forbidden = {token: xml.count(token) + svg.count(token) for token in ("#VALUE!", "#REF!")}
    if any(forbidden.values()):
        failures.append("forbidden ShapeSheet token")

    visible_records = visible_svg_text_and_fonts(svg)
    visible_text = " ".join(x["text"] for x in visible_records)
    bad_fonts = sorted({x["font"] for x in visible_records if x["font"] and x["font"].lower() not in {"segoe ui", "aptos"}})
    if bad_fonts:
        failures.append("visible forbidden fonts:" + ",".join(bad_fonts))
    for placeholder in ("成员名", "-成员名", "类名"):
        if placeholder in visible_text:
            failures.append("placeholder:" + placeholder)

    if re.search(r"<linearGradient\b", svg, re.I):
        failures.append("visible gradient")
    if re.search(r"<filter\b", svg, re.I):
        failures.append("visible filter/shadow")

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

        owners = {sid: semantic.get(sid) for sid in EXPECTED}
        if any(v is None for v in owners.values()):
            failures.append("missing class owner")
        if len(fields) != 5:
            failures.append("field count")

        class_master_ok = all(master_name(owner) == "Class" for owner in owners.values() if owner is not None)
        if not class_master_ok:
            failures.append("native Class master")

        owner_records = {}
        page_w = float(page.PageSheet.CellsU("PageWidth").Result("inches"))
        page_h = float(page.PageSheet.CellsU("PageHeight").Result("inches"))
        for sid, owner in owners.items():
            if owner is None:
                continue
            ob, header_h, body = body_bounds(owner)
            owner_text = subtree_text(owner)
            expected_stereo = EXPECTED[sid]["stereotype"]
            stereo_enabled = "TRUE" in formula(owner, "User.StereoType").upper()
            if not stereo_enabled or expected_stereo not in owner_text or expected_stereo not in visible_text:
                failures.append("native stereotype:" + sid)
            if ob["left"] < -1e-6 or ob["bottom"] < -1e-6 or ob["right"] > page_w + 1e-6 or ob["top"] > page_h + 1e-6:
                failures.append("owner outside page:" + sid)
            owner_records[sid] = {
                "shapeId": int(owner.ID),
                "master": master_name(owner),
                "boundsIn": ob,
                "headerHeightIn": header_h,
                "bodyBoundsIn": body,
                "nativeStereotype": expected_stereo,
            }

        # Empty default list artifacts may persist structurally, but they must be invisible.
        visible_default_artifacts = []
        for i in range(1, int(page.Shapes.Count) + 1):
            sh = page.Shapes.Item(i)
            m = master_name(sh)
            if m in {"Member", "Separator"}:
                line = formula(sh, "LinePattern")
                fill = formula(sh, "FillPattern")
                if text(sh).strip() or line not in {"", "0"} or fill not in {"", "0"}:
                    visible_default_artifacts.append({"shapeId": int(sh.ID), "master": m, "linePattern": line, "fillPattern": fill})
        if visible_default_artifacts:
            failures.append("visible default UML list artifacts")

        field_records = []
        by_owner = {sid: [] for sid in EXPECTED}
        for f in fields:
            sid, owner_sid = prop(f, "SpecId"), prop(f, "OwnerSpecId")
            order = int(prop(f, "FieldOrder") or "0")
            owner = owners.get(owner_sid)
            if owner is None or owner_sid not in by_owner:
                failures.append("field owner:" + sid)
                continue
            ob, header_h, body = body_bounds(owner)
            fb = eff(f)
            expected_fields = EXPECTED[owner_sid]["fields"]
            expected_text = expected_fields[order - 1] if 1 <= order <= len(expected_fields) else None
            if expected_text is None or text(f).strip() != expected_text:
                failures.append("field text/order:" + sid)
            inside_owner = fb["left"] >= ob["left"] - 1e-6 and fb["right"] <= ob["right"] + 1e-6 and fb["bottom"] >= ob["bottom"] - 1e-6 and fb["top"] <= ob["top"] + 1e-6
            in_body = inside_body(fb, body)
            x_formula, y_formula, w_formula = formula(f, "PinX"), formula(f, "PinY"), formula(f, "Width")
            owner_ref = str(owner.NameU)
            formula_text = x_formula + y_formula + w_formula
            formulas_ok = all(token in formula_text for token in (owner_ref + "!PinX", owner_ref + "!PinY", owner_ref + "!Width")) and owner_ref + "!User.HdrHgt" in y_formula
            fill, line = formula(f, "FillPattern"), formula(f, "LinePattern")
            char_color = formula(f, "Char.Color")
            font_formula = formula(f, "Char.Font")
            try:
                font_name = str(doc.Fonts.Item(int(font_formula)).Name)
            except Exception:
                font_name = ""
            if not (inside_owner and in_body):
                failures.append("field outside body:" + sid)
            if not formulas_ok:
                failures.append("anchor formula:" + sid)
            if fill != "0" or line != "0" or "RGB(15,23,42)" not in char_color or font_name not in {"Segoe UI", "Aptos"}:
                failures.append("field style:" + sid)
            by_owner[owner_sid].append(order)
            field_records.append({
                "specId": sid,
                "OwnerSpecId": owner_sid,
                "FieldOrder": order,
                "ownerShapeId": int(owner.ID),
                "ownerBoundsIn": ob,
                "headerHeightIn": header_h,
                "bodyBoundsIn": body,
                "fieldBoundsIn": fb,
                "insideOwner": inside_owner,
                "insideBody": in_body,
                "xFormula": x_formula,
                "yFormula": y_formula,
                "widthFormula": w_formula,
                "font": font_name,
                "textColor": char_color,
                "fillPattern": fill,
                "linePattern": line,
                "text": text(f),
            })

        for sid, orders in by_owner.items():
            expected_orders = list(range(1, len(EXPECTED[sid]["fields"]) + 1))
            if sorted(orders) != expected_orders:
                failures.append("field order sequence:" + sid)
        for i, a in enumerate(fields):
            for b in fields[i + 1:]:
                if prop(a, "OwnerSpecId") == prop(b, "OwnerSpecId") and overlap(eff(a), eff(b)):
                    failures.append("field overlap")

        # Move probe.
        anchor_probe = []
        for field in fields:
            owner = owners.get(prop(field, "OwnerSpecId"))
            if owner is None:
                continue
            before_field = eff(field)
            old_x = float(owner.CellsU("PinX").Result("inches"))
            old_y = float(owner.CellsU("PinY").Result("inches"))
            owner.CellsU("PinX").FormulaU = f"{old_x + 20 / 25.4} in"
            owner.CellsU("PinY").FormulaU = f"{old_y + 10 / 25.4} in"
            moved = eff(field)
            err = max(
                abs((moved["centerX"] - before_field["centerX"]) - 20 / 25.4),
                abs((moved["centerY"] - before_field["centerY"]) - 10 / 25.4),
            ) * 25.4
            anchor_probe.append({"field": prop(field, "SpecId"), "deltaErrorMm": err})
            owner.CellsU("PinX").FormulaU = f"{old_x} in"
            owner.CellsU("PinY").FormulaU = f"{old_y} in"
        anchor_status = "PASS" if max((x["deltaErrorMm"] for x in anchor_probe), default=0) <= TOL_MM else "FAIL"
        if anchor_status != "PASS":
            failures.append("move anchor behaviour")

        # Resize probe: verify width, body containment, order and overlap after mutation.
        resize_probe = []
        for owner_sid, owner in owners.items():
            if owner is None:
                continue
            old_w = float(owner.CellsU("Width").Result("inches"))
            old_h = float(owner.CellsU("Height").Result("inches"))
            owner.CellsU("Width").FormulaU = f"{old_w + 10 / 25.4} in"
            owner.CellsU("Height").FormulaU = f"{old_h + 8 / 25.4} in"
            new_ob, _, new_body = body_bounds(owner)
            owner_fields = sorted(
                [f for f in fields if prop(f, "OwnerSpecId") == owner_sid],
                key=lambda x: int(prop(x, "FieldOrder") or "0"),
            )
            measurements = []
            prev_y = None
            resize_ok = True
            for f in owner_fields:
                fb = eff(f)
                expected_width = new_ob["width"] - 0.16
                width_error_mm = abs(fb["width"] - expected_width) * 25.4
                center_error_mm = abs(fb["centerX"] - new_ob["centerX"]) * 25.4
                in_body = inside_body(fb, new_body)
                order_ok = prev_y is None or fb["centerY"] < prev_y
                prev_y = fb["centerY"]
                item_ok = width_error_mm <= TOL_MM and center_error_mm <= TOL_MM and in_body and order_ok
                resize_ok = resize_ok and item_ok
                measurements.append({
                    "field": prop(f, "SpecId"),
                    "centerXErrorMm": center_error_mm,
                    "widthErrorMm": width_error_mm,
                    "insideBody": in_body,
                    "orderPreserved": order_ok,
                })
            resize_overlap = any(overlap(eff(a), eff(b)) for i, a in enumerate(owner_fields) for b in owner_fields[i+1:])
            if resize_overlap:
                resize_ok = False
            resize_probe.append({"owner": owner_sid, "PASS": resize_ok, "overlap": resize_overlap, "fields": measurements})
            owner.CellsU("Width").FormulaU = f"{old_w} in"
            owner.CellsU("Height").FormulaU = f"{old_h} in"
        resize_status = "PASS" if all(x["PASS"] for x in resize_probe) else "FAIL"
        if resize_status != "PASS":
            failures.append("resize anchor behaviour")

        for owner_sid, spec in EXPECTED.items():
            for required in [owner_sid.replace("C2-", "").replace("-", ""), spec["stereotype"], *spec["fields"]]:
                # Class IDs are not used as literal text evidence. Actual class names checked below.
                pass
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
            "owners": owner_records,
            "fieldCount": len(fields),
            "fields": field_records,
            "visibleFonts": sorted({x["font"] for x in visible_records if x["font"]}),
            "visibleDefaultArtifacts": visible_default_artifacts,
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
