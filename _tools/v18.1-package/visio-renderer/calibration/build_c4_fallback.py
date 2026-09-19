"""C4 fallback calibration: native semantic Association + deterministic visible route overlay.

This file intentionally does NOT mutate Geometry1 on the native UML Association.

Semantic layer
--------------
- Microsoft UML Association master
- explicit side connection points
- BeginX / EndX glue remains live
- Prop.SpecId and source/target metadata remain authoritative
- native connector stroke is hidden only for presentation

Presentation layer
------------------
- one simple Visio line Shape per orthogonal route segment
- segment coordinates come directly from the approved route plan
- segment shapes are not glued and are not auto-routed
- every segment points back to its semantic Association through OwnerSpecId

The fallback is deliberately boring.  Boring is useful when Visio's connector
router keeps rebuilding Geometry rows that were supposed to be deterministic.
"""
from __future__ import annotations

import json
import os
import sys

import win32com.client
import yaml

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from presentation import cm_to_in  # noqa: E402
from render_core import load_master_map, resolve_font_id, set_prop  # noqa: E402
from routing_geometry import path_is_orthogonal, route_points  # noqa: E402
from style_adapter import apply_style  # noqa: E402

HERE = os.path.dirname(__file__)
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
OUT = os.path.join(HERE, "out")
SPEC_PATH = os.path.join(HERE, "c4-routing-calibration-spec.yaml")

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


def set_if_present(shape, cell_name: str, formula: str, *, required: bool = False) -> bool:
    try:
        if int(shape.CellExistsU(cell_name, 0)):
            force(shape.CellsU(cell_name), formula)
            return True
    except Exception:
        pass
    if required:
        raise RuntimeError(f"required ShapeSheet cell missing: {cell_name}")
    return False


def add_side_port(shape, side: str, fraction: float) -> dict:
    """Create one outward-facing instance connection point."""
    side = str(side).upper()
    f = float(fraction)
    if not 0.0 <= f <= 1.0:
        raise ValueError("port fraction must be in [0,1]")

    try:
        shape.AddSection(VIS_SECTION_CONNECTION)
    except Exception:
        pass

    tag_used = VIS_TAG_CONNECTION_POINT
    try:
        row = int(shape.AddRow(VIS_SECTION_CONNECTION, VIS_ROW_LAST, VIS_TAG_CONNECTION_POINT))
    except Exception:
        row = int(shape.AddRow(VIS_SECTION_CONNECTION, VIS_ROW_LAST, VIS_TAG_DEFAULT))
        tag_used = VIS_TAG_DEFAULT

    if side == "LEFT":
        x_formula, y_formula, dx, dy = "0", f"Height*{1.0-f}", -1, 0
    elif side == "RIGHT":
        x_formula, y_formula, dx, dy = "Width", f"Height*{1.0-f}", 1, 0
    elif side == "TOP":
        x_formula, y_formula, dx, dy = f"Width*{f}", "Height", 0, 1
    elif side == "BOTTOM":
        x_formula, y_formula, dx, dy = f"Width*{f}", "0", 0, -1
    else:
        raise ValueError(f"invalid side: {side}")

    x_cell = shape.CellsSRC(VIS_SECTION_CONNECTION, row, VIS_CNNCT_X)
    y_cell = shape.CellsSRC(VIS_SECTION_CONNECTION, row, VIS_CNNCT_Y)
    dirx_cell = shape.CellsSRC(VIS_SECTION_CONNECTION, row, VIS_CNNCT_DIRX)
    diry_cell = shape.CellsSRC(VIS_SECTION_CONNECTION, row, VIS_CNNCT_DIRY)
    type_cell = shape.CellsSRC(VIS_SECTION_CONNECTION, row, VIS_CNNCT_TYPE)

    force(x_cell, x_formula)
    force(y_cell, y_formula)
    force(dirx_cell, str(dx))
    force(diry_cell, str(dy))
    force(type_cell, "0")

    return {
        "rowIndex": row,
        "rowTagRequested": tag_used,
        "xCell": x_cell,
        "yCell": y_cell,
        "side": side,
        "fraction": f,
        "dir": [dx, dy],
    }


def style_overlay_segment(shape, tokens: dict) -> None:
    colour = tokens["colors"]["line"]
    line_style = tokens["lineStyles"]["association"]
    force(shape.CellsU("LinePattern"), "1")
    force(shape.CellsU("LineColor"), rgb_formula(colour))
    force(shape.CellsU("LineWeight"), f"{float(line_style['widthPt'])} pt")
    set_if_present(shape, "BeginArrow", "0")
    set_if_present(shape, "EndArrow", "0")
    set_if_present(shape, "FillPattern", "0")
    set_if_present(shape, "ShdwPattern", "0")
    set_if_present(shape, "GlowSize", "0")


def hide_semantic_connector(shape) -> None:
    """Hide only the semantic connector's stroke; retain the real UML object."""
    force(shape.CellsU("LinePattern"), "0")
    set_if_present(shape, "BeginArrow", "0")
    set_if_present(shape, "EndArrow", "0")
    set_if_present(shape, "ShdwPattern", "0")
    set_if_present(shape, "GlowSize", "0")


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
    page.NameU = "C4F_SemanticOverlay"
    force(page.PageSheet.CellsU("PageWidth"), f"{cm_to_in(page_w)} in")
    force(page.PageSheet.CellsU("PageHeight"), f"{cm_to_in(page_h)} in")

    nodes = {}
    stencil_docs = []
    build_routes = []
    stage = "initializing"
    active_route = None

    try:
        stage = "resolve-font"
        font_id = resolve_font_id(doc, "Segoe UI")

        # Native UML nodes
        for node in spec["nodes"]:
            stage = f"node:{node['id']}"
            kind = node["kind"]
            master_name = "Actor" if kind == "actor" else "Use Case"
            stencil_path = master_map["stencils"][master_name]["stencil"]
            stencil = next((s for s in stencil_docs if s.FullName == stencil_path), None)
            if stencil is None:
                stencil = app.Documents.OpenEx(stencil_path, 66)
                stencil_docs.append(stencil)

            shape = page.Drop(
                stencil.Masters.ItemU(master_name),
                *logical_to_page_in(node["x"], node["y"], page_h),
            )
            shape.Text = node["id"]
            set_prop(shape, "SpecId", node["id"])
            set_prop(shape, "Role", "semantic")
            set_prop(shape, "NodeKind", kind)

            style_ref = "actorHuman" if kind == "actor" else "useCaseDefault"
            apply_style(shape, node["id"], style_ref, tokens, font_id, [])

            force(shape.CellsU("Width"), f"{cm_to_in(float(node['width']))} in")
            force(shape.CellsU("Height"), f"{cm_to_in(float(node['height']))} in")
            px, py = logical_to_page_in(node["x"], node["y"], page_h)
            force(shape.CellsU("PinX"), f"{px} in")
            force(shape.CellsU("PinY"), f"{py} in")

            nodes[node["id"]] = {"shape": shape, "spec": node, "ports": {}}

        # Semantic relations + presentation routes
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

            stage = f"route:{active_route}:native-association"
            stencil_path = master_map["stencils"]["Association"]["stencil"]
            stencil = next((s for s in stencil_docs if s.FullName == stencil_path), None)
            if stencil is None:
                stencil = app.Documents.OpenEx(stencil_path, 66)
                stencil_docs.append(stencil)

            conn = page.Drop(stencil.Masters.ItemU("Association"), 1, 1)
            conn.Text = ""
            for key, value in {
                "SpecId": route["id"],
                "Role": "semantic",
                "ConnectorType": route["connectorType"],
                "SourceSpecId": route["source"],
                "TargetSpecId": route["target"],
                "SourceSide": route["sourceSide"],
                "TargetSide": route["targetSide"],
                "SourcePortFraction": route["sourcePortFraction"],
                "TargetPortFraction": route["targetPortFraction"],
                "Waypoints": json.dumps(route.get("waypoints", []), separators=(",", ":")),
                "RoutingMechanic": "native-semantic-hidden-plus-presentation-segments",
                "VisibleRouteSpecPrefix": f"{route['id']}::SEG::",
            }.items():
                set_prop(conn, key, value)

            # We no longer care how the semantic connector itself routes.
            # Its job is source/target semantics and live glue only.
            set_if_present(conn, "ShapeRouteStyle", "1")
            set_if_present(conn, "ConLineRouteExt", "0")
            conn.CellsU("BeginX").GlueTo(src["ports"][src_key]["xCell"])
            conn.CellsU("EndX").GlueTo(dst["ports"][dst_key]["xCell"])
            hide_semantic_connector(conn)

            stage = f"route:{active_route}:presentation-overlay"
            points = route_points(route, {k: v["spec"] for k, v in nodes.items()})
            if not path_is_orthogonal(points):
                raise RuntimeError(f"approved route is not orthogonal: {active_route}")

            segment_records = []
            segment_count = len(points) - 1
            for index, (a, b) in enumerate(zip(points, points[1:]), start=1):
                x1, y1 = logical_to_page_in(a[0], a[1], page_h)
                x2, y2 = logical_to_page_in(b[0], b[1], page_h)
                seg = page.DrawLine(x1, y1, x2, y2)
                seg.Text = ""

                seg_id = f"{active_route}::SEG::{index:02d}"
                set_prop(seg, "SpecId", seg_id)
                set_prop(seg, "Role", "presentation")
                set_prop(seg, "ContentRole", "route-segment")
                set_prop(seg, "OwnerSpecId", active_route)
                set_prop(seg, "SegmentIndex", index)
                set_prop(seg, "SegmentCount", segment_count)
                set_prop(seg, "StartCm", json.dumps(list(a), separators=(",", ":")))
                set_prop(seg, "EndCm", json.dumps(list(b), separators=(",", ":")))
                set_prop(seg, "RouteStyle", "association")
                style_overlay_segment(seg, tokens)

                segment_records.append({
                    "specId": seg_id,
                    "segmentIndex": index,
                    "startCm": list(a),
                    "endCm": list(b),
                })

            build_routes.append({
                "id": active_route,
                "semanticSpecId": active_route,
                "presentationSegmentCount": segment_count,
                "presentationSegments": segment_records,
                "plannedPointsCm": [list(p) for p in points],
            })

        active_route = None
        stage = "save-export"

        vsdx = os.path.join(OUT, "C4F_SemanticOverlay.vsdx")
        svg = os.path.join(OUT, "C4F_SemanticOverlay.raw.svg")
        png = os.path.join(OUT, "C4F_SemanticOverlay.png")

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

        with open(os.path.join(OUT, "C4F-build-record.json"), "w", encoding="utf-8") as handle:
            json.dump({
                "status": "BUILT",
                "strategy": "native-semantic-hidden-plus-presentation-segments",
                "routeCount": len(build_routes),
                "routes": build_routes,
            }, handle, ensure_ascii=False, indent=2)

        return 0

    except Exception as exc:
        with open(os.path.join(OUT, "C4F-build-record.json"), "w", encoding="utf-8") as handle:
            json.dump({
                "status": "FAIL",
                "stage": stage,
                "activeRoute": active_route,
                "error": repr(exc),
                "errorType": type(exc).__name__,
                "hresult": getattr(exc, "hresult", None),
                "excepinfo": getattr(exc, "excepinfo", None),
                "routes": build_routes,
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
