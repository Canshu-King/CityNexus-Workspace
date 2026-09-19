"""C4 Extend calibration.

Architecture under test:

- one genuine Microsoft UML `Extend` shape per semantic relation;
- the native semantic connector remains glued to explicit directional ports;
- only the semantic connector's visible stroke is hidden;
- the visible <<extend>> path is deterministic presentation geometry;
- only the final presentation segment owns the open target arrow;
- label and condition are separate presentation text shapes.

No native connector Geometry1 mutation is allowed.
"""
from __future__ import annotations

import json
import os
import sys

import win32com.client
import yaml

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from presentation import cm_to_in, rect_from_center, style_presentation_box, style_text  # noqa: E402
from render_core import load_master_map, resolve_font_id, set_prop  # noqa: E402
from routing_geometry import path_is_orthogonal, route_points  # noqa: E402
from style_adapter import apply_style  # noqa: E402

HERE = os.path.dirname(__file__)
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
OUT = os.path.join(HERE, "out")
SPEC_PATH = os.path.join(HERE, "c4-extend-calibration-spec.yaml")

VIS_SECTION_CONNECTION = 7
VIS_ROW_LAST = -2
VIS_TAG_CONNECTION_POINT = 153
VIS_TAG_DEFAULT = 0
VIS_CNNCT_X = 0
VIS_CNNCT_Y = 1
VIS_CNNCT_DIRX = 2
VIS_CNNCT_DIRY = 3
VIS_CNNCT_TYPE = 4


def force(cell, formula: str) -> None:
    try:
        cell.FormulaForceU = formula
    except Exception:
        cell.FormulaU = formula


def rgb_formula(hex_value: str) -> str:
    h = str(hex_value).lstrip("#")
    if len(h) != 6:
        raise ValueError(f"invalid colour: {hex_value}")
    r, g, b = (int(h[i:i+2], 16) for i in (0, 2, 4))
    return f"RGB({r},{g},{b})"


def logical_to_page_in(x_cm: float, y_cm: float, page_h_cm: float) -> tuple[float, float]:
    return cm_to_in(float(x_cm)), cm_to_in(float(page_h_cm) - float(y_cm))


def set_if_present(shape, cell_name: str, formula: str) -> bool:
    try:
        if int(shape.CellExistsU(cell_name, 0)):
            force(shape.CellsU(cell_name), formula)
            return True
    except Exception:
        pass
    return False


def effective_numeric(shape, cell_name: str, units: str = "") -> float:
    return float(shape.CellsU(cell_name).Result(units))


def add_side_port(shape, side: str, fraction: float) -> dict:
    side = str(side).upper()
    fraction = float(fraction)

    try:
        shape.AddSection(VIS_SECTION_CONNECTION)
    except Exception:
        pass

    try:
        row = int(shape.AddRow(VIS_SECTION_CONNECTION, VIS_ROW_LAST, VIS_TAG_CONNECTION_POINT))
        tag = VIS_TAG_CONNECTION_POINT
    except Exception:
        row = int(shape.AddRow(VIS_SECTION_CONNECTION, VIS_ROW_LAST, VIS_TAG_DEFAULT))
        tag = VIS_TAG_DEFAULT

    if side == "LEFT":
        x_formula, y_formula, dx, dy = "0", f"Height*{1.0-fraction}", -1, 0
    elif side == "RIGHT":
        x_formula, y_formula, dx, dy = "Width", f"Height*{1.0-fraction}", 1, 0
    elif side == "TOP":
        x_formula, y_formula, dx, dy = f"Width*{fraction}", "Height", 0, 1
    elif side == "BOTTOM":
        x_formula, y_formula, dx, dy = f"Width*{fraction}", "0", 0, -1
    else:
        raise ValueError(f"invalid side: {side}")

    x_cell = shape.CellsSRC(VIS_SECTION_CONNECTION, row, VIS_CNNCT_X)
    y_cell = shape.CellsSRC(VIS_SECTION_CONNECTION, row, VIS_CNNCT_Y)
    force(x_cell, x_formula)
    force(y_cell, y_formula)
    force(shape.CellsSRC(VIS_SECTION_CONNECTION, row, VIS_CNNCT_DIRX), str(dx))
    force(shape.CellsSRC(VIS_SECTION_CONNECTION, row, VIS_CNNCT_DIRY), str(dy))
    force(shape.CellsSRC(VIS_SECTION_CONNECTION, row, VIS_CNNCT_TYPE), "0")

    return {
        "rowIndex": row,
        "rowTag": tag,
        "xCell": x_cell,
        "yCell": y_cell,
        "side": side,
        "fraction": fraction,
        "dir": [dx, dy],
    }


def hide_semantic_connector(shape) -> None:
    force(shape.CellsU("LinePattern"), "0")
    set_if_present(shape, "ShdwPattern", "0")
    set_if_present(shape, "GlowSize", "0")


def apply_extend_segment_style(shape, tokens: dict, *, terminal: bool, arrow_code: int) -> None:
    line = tokens["lineStyles"]["includeExtend"]
    colour = tokens["colors"]["line"]

    force(shape.CellsU("LinePattern"), "2")
    force(shape.CellsU("LineColor"), rgb_formula(colour))
    force(shape.CellsU("LineWeight"), f"{float(line['widthPt'])} pt")
    set_if_present(shape, "BeginArrow", "0")
    set_if_present(shape, "EndArrow", str(int(arrow_code if terminal else 0)))
    set_if_present(shape, "ShdwPattern", "0")
    set_if_present(shape, "GlowSize", "0")


def native_open_arrow_code(shape) -> tuple[int, str]:
    candidates = []
    for cell_name in ("EndArrow", "BeginArrow"):
        try:
            code = int(round(float(shape.CellsU(cell_name).Result(""))))
        except Exception:
            code = 0
        candidates.append((code, cell_name))
    for code, cell_name in candidates:
        if code > 0:
            return code, cell_name
    raise RuntimeError("native Extend master exposes no non-zero arrow code")


def draw_text_box(page, box: dict, page_h_cm: float, text: str, *, spec_id: str,
                  owner_spec_id: str, content_role: str, font_id: int,
                  font_pt: float, text_color: str):
    left, bottom, right, top = rect_from_center(
        float(box["x"]), float(box["y"]), float(box["width"]), float(box["height"]), page_h_cm
    )
    shape = page.DrawRectangle(left, bottom, right, top)
    shape.Text = text
    set_prop(shape, "SpecId", spec_id)
    set_prop(shape, "Role", "presentation")
    set_prop(shape, "ContentRole", content_role)
    set_prop(shape, "OwnerSpecId", owner_spec_id)
    style_presentation_box(shape, fill=None, stroke=None)
    style_text(shape, font_id=font_id, color=text_color, size_pt=font_pt,
               horizontal="center", vertical="middle")
    return shape


def main() -> int:
    os.makedirs(OUT, exist_ok=True)

    with open(SPEC_PATH, encoding="utf-8") as handle:
        spec = yaml.safe_load(handle)
    with open(os.path.join(ROOT, "visio-spec", "style-tokens.yaml"), encoding="utf-8") as handle:
        tokens = yaml.safe_load(handle)

    page_h = float(spec["page"]["heightCm"])
    page_w = float(spec["page"]["widthCm"])
    master_map = load_master_map(os.path.join(ROOT, "visio-renderer", "native-master-map.json"))

    app = win32com.client.DispatchEx("Visio.Application")
    app.Visible = False
    app.AlertResponse = 7
    doc = app.Documents.Add("")
    page = doc.Pages.Item(1)
    page.NameU = spec["page"]["name"]
    force(page.PageSheet.CellsU("PageWidth"), f"{cm_to_in(page_w)} in")
    force(page.PageSheet.CellsU("PageHeight"), f"{cm_to_in(page_h)} in")

    stencil_docs = []
    nodes = {}
    records = []
    stage = "initializing"
    active_route = None

    try:
        font_id = resolve_font_id(doc, "Segoe UI")

        # Use cases.
        stencil_path = master_map["stencils"]["Use Case"]["stencil"]
        stencil = app.Documents.OpenEx(stencil_path, 66)
        stencil_docs.append(stencil)

        for node in spec["nodes"]:
            stage = f"node:{node['id']}"
            shape = page.Drop(
                stencil.Masters.ItemU("Use Case"),
                *logical_to_page_in(node["x"], node["y"], page_h),
            )
            shape.Text = node["text"]
            set_prop(shape, "SpecId", node["id"])
            set_prop(shape, "Role", "semantic")
            set_prop(shape, "NodeKind", "usecase")
            apply_style(shape, node["id"], node["styleRef"], tokens, font_id, [])
            force(shape.CellsU("Width"), f"{cm_to_in(float(node['width']))} in")
            force(shape.CellsU("Height"), f"{cm_to_in(float(node['height']))} in")
            px, py = logical_to_page_in(node["x"], node["y"], page_h)
            force(shape.CellsU("PinX"), f"{px} in")
            force(shape.CellsU("PinY"), f"{py} in")
            nodes[node["id"]] = {"shape": shape, "spec": node, "ports": {}}

        extend_stencil_path = master_map["stencils"]["Extend"]["stencil"]
        extend_stencil = next((s for s in stencil_docs if s.FullName == extend_stencil_path), None)
        if extend_stencil is None:
            extend_stencil = app.Documents.OpenEx(extend_stencil_path, 66)
            stencil_docs.append(extend_stencil)

        for route in spec["routes"]:
            active_route = route["id"]
            src = nodes[route["source"]]
            dst = nodes[route["target"]]

            stage = f"route:{active_route}:ports"
            src_key = (route["sourceSide"], float(route["sourcePortFraction"]))
            dst_key = (route["targetSide"], float(route["targetPortFraction"]))
            if src_key not in src["ports"]:
                src["ports"][src_key] = add_side_port(src["shape"], *src_key)
            if dst_key not in dst["ports"]:
                dst["ports"][dst_key] = add_side_port(dst["shape"], *dst_key)

            stage = f"route:{active_route}:native-extend"
            conn = page.Drop(extend_stencil.Masters.ItemU("Extend"), 1, 1)
            native_arrow_code, arrow_source_cell = native_open_arrow_code(conn)
            conn.Text = ""

            for key, value in {
                "SpecId": route["id"],
                "Role": "semantic",
                "ConnectorType": "extend",
                "SourceSpecId": route["source"],
                "TargetSpecId": route["target"],
                "SourceSide": route["sourceSide"],
                "TargetSide": route["targetSide"],
                "SourcePortFraction": route["sourcePortFraction"],
                "TargetPortFraction": route["targetPortFraction"],
                "NativeArrowCode": native_arrow_code,
                "NativeArrowSourceCell": arrow_source_cell,
                "RoutingMechanic": "native-extend-hidden-plus-presentation-segments",
            }.items():
                set_prop(conn, key, value)

            conn.CellsU("BeginX").GlueTo(src["ports"][src_key]["xCell"])
            conn.CellsU("EndX").GlueTo(dst["ports"][dst_key]["xCell"])
            hide_semantic_connector(conn)

            stage = f"route:{active_route}:presentation-path"
            points = route_points(route, {k: v["spec"] for k, v in nodes.items()})
            if not path_is_orthogonal(points):
                raise RuntimeError(f"approved extend path is not orthogonal: {active_route}")

            segment_records = []
            segment_count = len(points) - 1
            for index, (a, b) in enumerate(zip(points, points[1:]), start=1):
                x1, y1 = logical_to_page_in(a[0], a[1], page_h)
                x2, y2 = logical_to_page_in(b[0], b[1], page_h)
                seg = page.DrawLine(x1, y1, x2, y2)
                seg.Text = ""
                seg_id = f"{active_route}::SEG::{index:02d}"

                for key, value in {
                    "SpecId": seg_id,
                    "Role": "presentation",
                    "ContentRole": "extend-route-segment",
                    "OwnerSpecId": active_route,
                    "SegmentIndex": index,
                    "SegmentCount": segment_count,
                    "TerminalSegment": str(index == segment_count).lower(),
                    "StartCm": json.dumps(list(a), separators=(",", ":")),
                    "EndCm": json.dumps(list(b), separators=(",", ":")),
                    "RouteStyle": "includeExtend",
                }.items():
                    set_prop(seg, key, value)

                apply_extend_segment_style(
                    seg,
                    tokens,
                    terminal=index == segment_count,
                    arrow_code=native_arrow_code,
                )
                segment_records.append({
                    "specId": seg_id,
                    "segmentIndex": index,
                    "startCm": list(a),
                    "endCm": list(b),
                    "terminal": index == segment_count,
                })

            stage = f"route:{active_route}:labels"
            text_color = tokens["colors"][spec["style"]["textColor"]]
            draw_text_box(
                page, route["labelBox"], page_h, route["label"],
                spec_id=f"{active_route}::LABEL",
                owner_spec_id=active_route,
                content_role="extend-label",
                font_id=font_id,
                font_pt=float(spec["style"]["labelFontPt"]),
                text_color=text_color,
            )
            draw_text_box(
                page, route["conditionBox"], page_h, route["condition"],
                spec_id=f"{active_route}::CONDITION",
                owner_spec_id=active_route,
                content_role="extend-condition",
                font_id=font_id,
                font_pt=float(spec["style"]["conditionFontPt"]),
                text_color=text_color,
            )

            records.append({
                "id": active_route,
                "nativeMaster": "Extend",
                "nativeArrowCode": native_arrow_code,
                "nativeArrowSourceCell": arrow_source_cell,
                "plannedPointsCm": [list(p) for p in points],
                "presentationSegmentCount": segment_count,
                "presentationSegments": segment_records,
                "label": route["label"],
                "condition": route["condition"],
            })

        active_route = None
        stage = "save-export"

        vsdx = os.path.join(OUT, "C4E_ExtendFallback.vsdx")
        svg = os.path.join(OUT, "C4E_ExtendFallback.raw.svg")
        png = os.path.join(OUT, "C4E_ExtendFallback.png")

        doc.SaveAs(vsdx)
        page.Export(svg)
        page.Export(png)

        try:
            from PIL import Image
            image = Image.open(png)
            if image.width < 1600:
                target_w = 1600
                target_h = round(image.height * target_w / image.width)
                image.resize((target_w, target_h), Image.Resampling.LANCZOS).save(png)
        except Exception:
            pass

        with open(os.path.join(OUT, "C4E-build-record.json"), "w", encoding="utf-8") as handle:
            json.dump({
                "status": "BUILT",
                "strategy": "native-extend-hidden-plus-presentation-segments",
                "routeCount": len(records),
                "routes": records,
            }, handle, ensure_ascii=False, indent=2)

        return 0

    except Exception as exc:
        with open(os.path.join(OUT, "C4E-build-record.json"), "w", encoding="utf-8") as handle:
            json.dump({
                "status": "FAIL",
                "stage": stage,
                "activeRoute": active_route,
                "error": repr(exc),
                "errorType": type(exc).__name__,
                "hresult": getattr(exc, "hresult", None),
                "excepinfo": getattr(exc, "excepinfo", None),
                "routes": records,
            }, handle, ensure_ascii=False, indent=2, default=str)
        raise

    finally:
        try:
            doc.Saved = True
            doc.Close()
        except Exception:
            pass
        for stencil in stencil_docs:
            try:
                stencil.Close()
            except Exception:
                pass
        try:
            app.Quit()
        except Exception:
            pass


if __name__ == "__main__":
    raise SystemExit(main())
