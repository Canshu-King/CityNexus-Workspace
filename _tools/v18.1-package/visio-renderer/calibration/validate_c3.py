"""Independent validator for the C3 presentation-layer calibration."""
from __future__ import annotations

import html
import json
import os
import re
import zipfile

import win32com.client
import yaml

HERE = os.path.dirname(__file__)
OUT = os.path.join(HERE, "out")
SPEC_PATH = os.path.join(HERE, "c3-presentation-spec.yaml")
VSDX = os.path.join(OUT, "C3_Presentation.vsdx")
SVG = os.path.join(OUT, "C3_Presentation.raw.svg")
REPORT = os.path.join(OUT, "C3_Presentation-report.json")
TOL_IN = 0.5 / 25.4


def prop(shape, name: str) -> str:
    try:
        return str(shape.CellsU("Prop." + name).ResultStr(20)).strip('"')
    except Exception:
        try:
            return str(shape.CellsU("Prop." + name).FormulaU).strip('"')
        except Exception:
            return ""


def formula(shape, cell: str) -> str:
    try:
        return str(shape.CellsU(cell).FormulaU)
    except Exception:
        return ""


def result(shape, cell: str) -> float:
    return float(shape.CellsU(cell).Result("inches"))


def bounds(shape) -> dict[str, float]:
    pin_x, pin_y = result(shape, "PinX"), result(shape, "PinY")
    loc_x, loc_y = result(shape, "LocPinX"), result(shape, "LocPinY")
    width, height = result(shape, "Width"), result(shape, "Height")
    left, bottom = pin_x - loc_x, pin_y - loc_y
    return {"left": left, "bottom": bottom, "right": left + width, "top": bottom + height,
            "width": width, "height": height, "centerX": left + width / 2, "centerY": bottom + height / 2}


def hex_to_rgb_formula(value: str) -> str:
    h = value.lstrip("#")
    r, g, b = (int(h[i:i+2], 16) for i in (0, 2, 4))
    return f"RGB({r},{g},{b})"


def intersects(a, b) -> bool:
    return min(a["right"], b["right"]) > max(a["left"], b["left"]) and min(a["top"], b["top"]) > max(a["bottom"], b["bottom"])


def visible_svg_text(svg: str) -> tuple[list[dict], list[str]]:
    css = {m.group(1): m.group(2) for m in re.finditer(r"\.(st\d+)\s*\{([^}]*)\}", svg, re.I | re.S)}
    records = []
    forbidden_fonts = []
    for m in re.finditer(r'<text([^>]*)>(.*?)</text>', svg, re.I | re.S):
        attrs = m.group(1)
        raw = re.sub(r"<[^>]+>", "", m.group(2))
        text = html.unescape(raw).strip()
        cls_m = re.search(r'class="([^"]+)"', attrs)
        cls = cls_m.group(1).split()[0] if cls_m else ""
        style = css.get(cls, "")
        fam_m = re.search(r"font-family:([^;}]+)", style, re.I)
        family = fam_m.group(1).strip() if fam_m else ""
        if family and family.lower() not in {"segoe ui", "aptos"}:
            forbidden_fonts.append(family)
        records.append({"text": text, "class": cls, "font": family})
    return records, forbidden_fonts


def main() -> int:
    failures: list[str] = []
    spec = yaml.safe_load(open(SPEC_PATH, encoding="utf-8"))
    expected = {x["id"]: x for x in spec["presentation"]}
    if not os.path.exists(VSDX) or not os.path.exists(SVG):
        failures.append("missing C3 artifacts")
        payload = {"calibration": "C3", "status": "FAIL", "failures": failures}
        json.dump(payload, open(REPORT, "w", encoding="utf-8"), indent=2)
        return 1

    with zipfile.ZipFile(VSDX) as z:
        xml = "\n".join(z.read(n).decode("utf-8", "ignore") for n in z.namelist() if n.endswith(".xml"))
    svg = open(SVG, encoding="utf-8", errors="ignore").read()
    for token in ("#VALUE!", "#REF!"):
        if token in xml or token in svg:
            failures.append("forbidden ShapeSheet token: " + token)
    if re.search(r"<linearGradient\b", svg, re.I):
        failures.append("visible gradient")
    if re.search(r"<filter\b", svg, re.I):
        failures.append("visible filter/shadow")
    svg_text, forbidden_fonts = visible_svg_text(svg)
    if forbidden_fonts:
        failures.append("forbidden visible font: " + ",".join(sorted(set(forbidden_fonts))))
    all_svg_text = " ".join(x["text"] for x in svg_text)

    app = win32com.client.DispatchEx("Visio.Application")
    app.Visible = False
    app.AlertResponse = 7
    doc = app.Documents.Open(VSDX)
    records = {}
    out_of_bounds = []
    overlaps = []
    try:
        page = doc.Pages.Item(1)
        page_w = float(page.PageSheet.CellsU("PageWidth").Result("inches"))
        page_h = float(page.PageSheet.CellsU("PageHeight").Result("inches"))
        exp_w = float(spec["page"]["widthCm"]) / 2.54
        exp_h = float(spec["page"]["heightCm"]) / 2.54
        if abs(page_w - exp_w) > TOL_IN or abs(page_h - exp_h) > TOL_IN:
            failures.append("page dimensions")

        actual = {}
        for i in range(1, int(page.Shapes.Count) + 1):
            sh = page.Shapes.Item(i)
            sid = prop(sh, "SpecId")
            if sid:
                if sid in actual:
                    failures.append("duplicate SpecId:" + sid)
                actual[sid] = sh
        if set(actual) != set(expected):
            failures.append("presentation SpecId set")

        for sid, item in expected.items():
            sh = actual.get(sid)
            if sh is None:
                continue
            b = bounds(sh)
            if b["left"] < -TOL_IN or b["bottom"] < -TOL_IN or b["right"] > page_w + TOL_IN or b["top"] > page_h + TOL_IN:
                out_of_bounds.append(sid)
            exp_x = float(item["x"]) / 2.54
            exp_y = (float(spec["page"]["heightCm"]) - float(item["y"])) / 2.54
            exp_width = float(item["width"]) / 2.54
            exp_height = float(item["height"]) / 2.54
            pos_delta_mm = max(abs(b["centerX"] - exp_x), abs(b["centerY"] - exp_y)) * 25.4
            size_delta_mm = max(abs(b["width"] - exp_width), abs(b["height"] - exp_height)) * 25.4
            if pos_delta_mm > 0.5:
                failures.append("position:" + sid)
            if size_delta_mm > 0.5:
                failures.append("size:" + sid)
            if prop(sh, "Role") != "presentation" or prop(sh, "ContentRole") != item["role"]:
                failures.append("role:" + sid)

            fill_pattern = formula(sh, "FillPattern")
            line_pattern = formula(sh, "LinePattern")
            if item.get("fill") is None:
                if fill_pattern != "0": failures.append("fill pattern:" + sid)
            else:
                if fill_pattern != "1" or hex_to_rgb_formula(item["fill"]) not in formula(sh, "FillForegnd"):
                    failures.append("fill:" + sid)
            if item.get("stroke") is None:
                if line_pattern != "0": failures.append("line pattern:" + sid)
            else:
                if line_pattern != "1" or hex_to_rgb_formula(item["stroke"]) not in formula(sh, "LineColor"):
                    failures.append("stroke:" + sid)
            if item.get("text"):
                if item["text"].splitlines()[0] not in all_svg_text:
                    failures.append("missing SVG text:" + sid)
                font_formula = formula(sh, "Char.Font")
                try:
                    font_name = str(doc.Fonts.Item(int(font_formula)).Name)
                except Exception:
                    font_name = ""
                if font_name not in {"Segoe UI", "Aptos"}:
                    failures.append("font:" + sid)
                if hex_to_rgb_formula(item["textColor"]) not in formula(sh, "Char.Color"):
                    failures.append("text colour:" + sid)
            records[sid] = {
                "boundsIn": b,
                "positionDeltaMm": pos_delta_mm,
                "sizeDeltaMm": size_delta_mm,
                "fillPattern": fill_pattern,
                "linePattern": line_pattern,
            }

        # The canvas must exactly cover the page. All other presentation shapes
        # must not overlap each other except by explicit design; C3 has none.
        bg = records.get("BG-CANVAS", {}).get("boundsIn")
        if bg is None or max(abs(bg["left"]), abs(bg["bottom"]), abs(bg["right"] - page_w), abs(bg["top"] - page_h)) > TOL_IN:
            failures.append("canvas bounds")
        non_bg = [sid for sid in expected if sid != "BG-CANVAS" and sid in records]
        for i, a in enumerate(non_bg):
            for b in non_bg[i+1:]:
                if intersects(records[a]["boundsIn"], records[b]["boundsIn"]):
                    overlaps.append([a, b])
        if overlaps:
            failures.append("presentation overlap")
        if out_of_bounds:
            failures.append("presentation out of bounds")
    finally:
        try:
            doc.Saved = True
        except Exception:
            pass
        doc.Close()
        app.Quit()

    payload = {
        "calibration": "C3",
        "status": "PASS" if not failures else "FAIL",
        "artifact": os.path.basename(VSDX),
        "rawSvg": os.path.basename(SVG),
        "expectedPresentationCount": len(expected),
        "records": records,
        "outOfBounds": out_of_bounds,
        "overlaps": overlaps,
        "visibleSvgText": svg_text,
        "failures": failures,
    }
    with open(REPORT, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    # Windows PowerShell may expose a GBK stdout; ASCII JSON keeps the
    # validator exit status independent of console code page.
    print(json.dumps(payload, ensure_ascii=True, indent=2))
    return 0 if payload["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
