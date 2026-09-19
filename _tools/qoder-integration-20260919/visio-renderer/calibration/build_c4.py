"""Build the isolated C4 explicit-port/waypoint calibration document."""
from __future__ import annotations

import json
import os
import sys

import win32com.client
import yaml

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from presentation import cm_to_in  # noqa: E402
from render_core import load_master_map, set_prop  # noqa: E402
from routing_geometry import route_points  # noqa: E402
from style_adapter import apply_style  # noqa: E402

HERE = os.path.dirname(__file__)
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
OUT = os.path.join(HERE, "out")
SPEC_PATH = os.path.join(HERE, "c4-routing-calibration-spec.yaml")


def force(cell, formula: str) -> None:
    try:
        cell.FormulaForceU = formula
    except Exception:
        cell.FormulaU = formula


def logical_to_visio(x_cm, y_cm, page_h_cm):
    return cm_to_in(float(x_cm)), cm_to_in(float(page_h_cm) - float(y_cm))


def add_side_port(shape, side: str, fraction: float) -> str:
    try:
        shape.AddSection(7)
    except Exception:
        pass
    shape.AddRow(7, -1, 0)
    row = int(shape.RowCount(7))
    force(shape.CellsU(f"Connections.X{row}"), "0" if side == "LEFT" else "Width")
    # Connection-point Y is bottom-origin; the YAML fraction is top-origin.
    force(shape.CellsU(f"Connections.Y{row}"), f"Height*{1.0 - float(fraction)}")
    return f"Connections.X{row}"


def set_geometry_rows(connector, logical_points, page_h_cm):
    print("C4: geometry points", len(logical_points), flush=True)
    visio_points = [logical_to_visio(x, y, page_h_cm) for x, y in logical_points]
    min_x = min(x for x, _ in visio_points)
    min_y = min(y for _, y in visio_points)
    # Native Association starts with three Geometry1 rows (MoveTo, LineTo,
    # terminal row).  Add only the deterministic number of extra vertices;
    # querying RowCount while Visio recalculates a connector can otherwise
    # return a stale value and spin forever.
    existing = 3
    print("C4: geometry rowcount", existing, flush=True)
    for _ in range(max(0, len(visio_points) - existing)):
        print("C4: add geometry row", flush=True)
        connector.AddRow(10, -1, 0)
    for idx, (x, y) in enumerate(visio_points, 1):
        print("C4: set geometry row", idx, flush=True)
        force(connector.CellsU(f"Geometry1.X{idx}"), f"{x - min_x} in")
        force(connector.CellsU(f"Geometry1.Y{idx}"), f"{y - min_y} in")


def main() -> int:
    print("C4: loading spec", flush=True)
    spec = yaml.safe_load(open(SPEC_PATH, encoding="utf-8"))
    page_h = float(spec["page"]["heightCm"])
    master_map = load_master_map(os.path.join(ROOT, "visio-renderer", "native-master-map.json"))
    app = win32com.client.DispatchEx("Visio.Application")
    print("C4: Visio instance", flush=True)
    app.Visible = False
    app.AlertResponse = 7
    doc = app.Documents.Add("")
    page = doc.Pages.Item(1)
    page.NameU = "C4_Routing"
    force(page.PageSheet.CellsU("PageWidth"), f"{cm_to_in(float(spec['page']['widthCm']))} in")
    force(page.PageSheet.CellsU("PageHeight"), f"{cm_to_in(page_h)} in")
    nodes = {}
    connectors = []
    stencil_docs = []
    try:
        font_id = None
        for node in spec["nodes"]:
            print(f"C4: node {node['id']}", flush=True)
            kind = node["kind"]
            master_name = "Actor" if kind == "actor" else "Use Case"
            stencil_path = master_map["stencils"][master_name]["stencil"]
            stencil = next((x for x in stencil_docs if x.FullName == stencil_path), None)
            if stencil is None:
                stencil = app.Documents.OpenEx(stencil_path, 66)
                stencil_docs.append(stencil)
            shape = page.Drop(stencil.Masters.ItemU(master_name), *logical_to_visio(node["x"], node["y"], page_h))
            shape.Text = node["id"]
            set_prop(shape, "SpecId", node["id"])
            set_prop(shape, "Role", "semantic")
            set_prop(shape, "NodeKind", kind)
            set_prop(shape, "SourceYamlId", node["id"])
            # Apply the calibrated native style to the actual master instance.
            style_ref = "actorHuman" if kind == "actor" else "useCaseDefault"
            tokens = yaml.safe_load(open(os.path.join(ROOT, "visio-spec", "style-tokens.yaml"), encoding="utf-8"))
            if font_id is None:
                from render_core import resolve_font_id
                font_id = resolve_font_id(doc, "Segoe UI")
            apply_style(shape, node["id"], style_ref, tokens, font_id, [])
            # Only instance connection points are added; masters remain untouched.
            nodes[node["id"]] = {"shape": shape, "spec": node, "ports": {}}

        for route in spec["routes"]:
            print(f"C4: route {route['id']}", flush=True)
            src = nodes[route["source"]]
            dst = nodes[route["target"]]
            print("C4: ports", flush=True)
            src_port = src["ports"].setdefault((route["sourceSide"], route["sourcePortFraction"]), add_side_port(src["shape"], route["sourceSide"], route["sourcePortFraction"]))
            dst_port = dst["ports"].setdefault((route["targetSide"], route["targetPortFraction"]), add_side_port(dst["shape"], route["targetSide"], route["targetPortFraction"]))
            print("C4: ports ready", src_port, dst_port, flush=True)
            stencil_path = master_map["stencils"]["Association"]["stencil"]
            stencil = next((x for x in stencil_docs if x.FullName == stencil_path), None)
            if stencil is None:
                stencil = app.Documents.OpenEx(stencil_path, 66)
                stencil_docs.append(stencil)
            conn = page.Drop(stencil.Masters.ItemU("Association"), 1, 1)
            print("C4: connector dropped", flush=True)
            conn.Text = ""
            set_prop(conn, "SpecId", route["id"])
            set_prop(conn, "Role", "semantic")
            set_prop(conn, "ConnectorType", route["connectorType"])
            set_prop(conn, "SourceSpecId", route["source"])
            set_prop(conn, "TargetSpecId", route["target"])
            set_prop(conn, "SourceSide", route["sourceSide"])
            set_prop(conn, "TargetSide", route["targetSide"])
            set_prop(conn, "SourcePortFraction", route["sourcePortFraction"])
            set_prop(conn, "TargetPortFraction", route["targetPortFraction"])
            set_prop(conn, "Waypoints", json.dumps(route.get("waypoints", []), separators=(",", ":")))
            print("C4: geometry", flush=True)
            set_geometry_rows(conn, route_points(route, {k: v["spec"] for k, v in nodes.items()}), page_h)
            print("C4: geometry ready", flush=True)
            # Glue only after the one native connector's geometry is present;
            # Visio otherwise recalculates the Geometry section while rows are
            # being appended and can deadlock the automation server.
            conn.CellsU("BeginX").GlueTo(src["shape"].CellsU(src_port))
            print("C4: begin glued", flush=True)
            conn.CellsU("EndX").GlueTo(dst["shape"].CellsU(dst_port))
            print("C4: end glued", flush=True)
            connectors.append(conn)

        vsdx = os.path.join(OUT, "C4_Routing.vsdx")
        svg = os.path.join(OUT, "C4_Routing.raw.svg")
        png = os.path.join(OUT, "C4_Routing.png")
        print("C4: save", flush=True)
        doc.SaveAs(vsdx)
        print("C4: export", flush=True)
        page.Export(svg)
        page.Export(png)
        # Visio's default raster export is often <1600px wide. Upscale only
        # the review PNG; the raw SVG remains the authoritative export.
        try:
            from PIL import Image
            image = Image.open(png)
            if image.width < 1600:
                target_w = 1600
                target_h = round(image.height * target_w / image.width)
                image.resize((target_w, target_h), Image.Resampling.LANCZOS).save(png)
        except Exception:
            pass
        print(json.dumps({"status": "BUILT", "nodes": len(nodes), "connectors": len(connectors), "fontId": font_id}, ensure_ascii=True))
        return 0
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
