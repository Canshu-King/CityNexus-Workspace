"""C4.1: realize explicit waypoints on ONE native UML Association connector.

This is intentionally separate from the historical failed C4 build.
The critical order is:
  1) create native nodes and directional instance connection points;
  2) drop a native Association;
  3) override the master's center-to-center/straight routing cells locally;
  4) disable automatic rerouting and glue both endpoints;
  5) write Geometry1 AFTER glue, using the connector's actual local transform.

If Visio still rewrites the Geometry rows, the independent C4.1 validator must
fail.  No renderer-authored PASS is produced here.
"""
from __future__ import annotations

import json
import math
import os
import sys

import win32com.client
import yaml

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from presentation import cm_to_in  # noqa: E402
from render_core import load_master_map, resolve_font_id, set_prop  # noqa: E402
from routing_geometry import route_points  # noqa: E402
from style_adapter import apply_style  # noqa: E402

HERE = os.path.dirname(__file__)
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
OUT = os.path.join(HERE, "out")
SPEC_PATH = os.path.join(HERE, "c4-routing-calibration-spec.yaml")

VIS_SECTION_CONNECTION = 7
VIS_SECTION_GEOMETRY_1 = 10
VIS_ROW_LAST = -1
VIS_TAG_CONNECTION_POINT = 153
VIS_TAG_LINE_TO = 139


def force(cell, formula: str) -> None:
    try:
        cell.FormulaForceU = formula
    except Exception:
        cell.FormulaU = formula


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
    """Add an instance connection point with an outward orientation vector."""
    side = str(side).upper()
    f = float(fraction)
    if not 0.0 <= f <= 1.0:
        raise ValueError("port fraction must be in [0,1]")
    try:
        shape.AddSection(VIS_SECTION_CONNECTION)
    except Exception:
        pass
    row = int(shape.AddRow(VIS_SECTION_CONNECTION, VIS_ROW_LAST, VIS_TAG_CONNECTION_POINT))

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

    force(shape.CellsU(f"Connections.X{row}"), x_formula)
    force(shape.CellsU(f"Connections.Y{row}"), y_formula)
    # Direction cells influence the attached leg of a dynamic/right-angle connector.
    set_if_present(shape, f"Connections.DirX{row}", str(dx))
    set_if_present(shape, f"Connections.DirY{row}", str(dy))
    set_if_present(shape, f"Connections.Type{row}", "0")  # inward connection point
    return {
        "row": row,
        "xCell": f"Connections.X{row}",
        "yCell": f"Connections.Y{row}",
        "side": side,
        "fraction": f,
        "dir": [dx, dy],
    }


def page_to_local(connector, page_x: float, page_y: float) -> tuple[float, float]:
    """Inverse of the Visio Shape transform using effective Pin/LocPin/Angle."""
    pin_x = float(connector.CellsU("PinX").Result("inches"))
    pin_y = float(connector.CellsU("PinY").Result("inches"))
    loc_x = float(connector.CellsU("LocPinX").Result("inches"))
    loc_y = float(connector.CellsU("LocPinY").Result("inches"))
    angle = float(connector.CellsU("Angle").Result("radians"))
    dx = float(page_x) - pin_x
    dy = float(page_y) - pin_y
    c, s = math.cos(angle), math.sin(angle)
    # inverse rotation + translation
    return loc_x + c * dx + s * dy, loc_y - s * dx + c * dy


def geometry_row_exists(connector, ix: int) -> bool:
    try:
        return bool(int(connector.CellExistsU(f"Geometry1.X{ix}", 0)))
    except Exception:
        return False


def write_geometry_after_glue(connector, logical_points, page_h_cm: float) -> list[dict]:
    """Write an exact polyline into Geometry1 after glue/reroute has been frozen."""
    if len(logical_points) < 2:
        raise ValueError("route needs at least two points")

    page_points = [logical_to_page_in(x, y, page_h_cm) for x, y in logical_points]
    local_points = [page_to_local(connector, x, y) for x, y in page_points]

    # A freshly dropped native Association has MoveTo row 1 and LineTo row 2.
    # If Visio already expanded the geometry before this explicit write, fail
    # rather than silently mixing router-generated and requested vertices.
    if not geometry_row_exists(connector, 1) or not geometry_row_exists(connector, 2):
        raise RuntimeError("native Association Geometry1 rows 1/2 unavailable")
    if geometry_row_exists(connector, 3):
        raise RuntimeError("unexpected pre-existing Geometry1 row 3 before manual realization")

    force(connector.CellsU("Geometry1.X1"), f"{local_points[0][0]} in")
    force(connector.CellsU("Geometry1.Y1"), f"{local_points[0][1]} in")
    force(connector.CellsU("Geometry1.X2"), f"{local_points[1][0]} in")
    force(connector.CellsU("Geometry1.Y2"), f"{local_points[1][1]} in")

    rows = [1, 2]
    for local_x, local_y in local_points[2:]:
        ix = int(connector.AddRow(VIS_SECTION_GEOMETRY_1, VIS_ROW_LAST, VIS_TAG_LINE_TO))
        force(connector.CellsU(f"Geometry1.X{ix}"), f"{local_x} in")
        force(connector.CellsU(f"Geometry1.Y{ix}"), f"{local_y} in")
        rows.append(ix)

    return [
        {
            "row": ix,
            "localIn": [local_points[pos][0], local_points[pos][1]],
            "pageIn": [page_points[pos][0], page_points[pos][1]],
        }
        for pos, ix in enumerate(rows)
    ]


def main() -> int:
    os.makedirs(OUT, exist_ok=True)
    with open(SPEC_PATH, encoding="utf-8") as handle:
        spec = yaml.safe_load(handle)
    page_h = float(spec["page"]["heightCm"])
    master_map = load_master_map(os.path.join(ROOT, "visio-renderer", "native-master-map.json"))
    with open(os.path.join(ROOT, "visio-spec", "style-tokens.yaml"), encoding="utf-8") as handle:
        tokens = yaml.safe_load(handle)

    app = win32com.client.DispatchEx("Visio.Application")
    app.Visible = False
    app.AlertResponse = 7
    doc = app.Documents.Add("")
    page = doc.Pages.Item(1)
    page.NameU = "C4_1_Routing"
    force(page.PageSheet.CellsU("PageWidth"), f"{cm_to_in(float(spec['page']['widthCm']))} in")
    force(page.PageSheet.CellsU("PageHeight"), f"{cm_to_in(page_h)} in")

    # Disable advanced automatic connector routing while exact native geometry
    # is being installed.  Endpoint glue remains live, but Visio should not
    # replace the requested route merely because a connector is glued.
    route_passive_set = False
    try:
        page.LayoutRoutePassive = True
        route_passive_set = True
    except Exception:
        pass

    nodes = {}
    stencil_docs = []
    build_records = []
    try:
        font_id = resolve_font_id(doc, "Segoe UI")
        for node in spec["nodes"]:
            kind = node["kind"]
            master_name = "Actor" if kind == "actor" else "Use Case"
            stencil_path = master_map["stencils"][master_name]["stencil"]
            stencil = next((x for x in stencil_docs if x.FullName == stencil_path), None)
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

            # C4 route planning is expressed against the node boxes in the
            # calibration YAML.  The native Actor master has a different
            # inherited width, so the old C4 glued to a real side port that did
            # not coincide with the planned side port.  Freeze the exact spec
            # geometry before creating connection points.
            force(shape.CellsU("Width"), f"{cm_to_in(float(node['width']))} in")
            force(shape.CellsU("Height"), f"{cm_to_in(float(node['height']))} in")
            px, py = logical_to_page_in(node["x"], node["y"], page_h)
            force(shape.CellsU("PinX"), f"{px} in")
            force(shape.CellsU("PinY"), f"{py} in")
            nodes[node["id"]] = {"shape": shape, "spec": node, "ports": {}}

        for route in spec["routes"]:
            src = nodes[route["source"]]
            dst = nodes[route["target"]]
            src_key = (route["sourceSide"], float(route["sourcePortFraction"]))
            dst_key = (route["targetSide"], float(route["targetPortFraction"]))
            if src_key not in src["ports"]:
                src["ports"][src_key] = add_side_port(src["shape"], *src_key)
            if dst_key not in dst["ports"]:
                dst["ports"][dst_key] = add_side_port(dst["shape"], *dst_key)
            src_port = src["ports"][src_key]
            dst_port = dst["ports"][dst_key]

            stencil_path = master_map["stencils"]["Association"]["stencil"]
            stencil = next((x for x in stencil_docs if x.FullName == stencil_path), None)
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
                "RoutingMechanic": "manual-geometry-after-glue",
            }.items():
                set_prop(conn, key, value)

            # The stock UML Association master is centre-to-centre + straight.
            # Override those inherited values on the instance before glue.
            set_if_present(conn, "ShapeRouteStyle", "1", required=True)   # right angle
            set_if_present(conn, "ConLineRouteExt", "0", required=True)  # page/default extension, not forced straight
            set_if_present(conn, "ConFixedCode", "2")                    # never reroute

            conn.CellsU("BeginX").GlueTo(src["shape"].CellsU(src_port["xCell"]))
            conn.CellsU("EndX").GlueTo(dst["shape"].CellsU(dst_port["xCell"]))

            planned = route_points(route, {k: v["spec"] for k, v in nodes.items()})
            rows = write_geometry_after_glue(conn, planned, page_h)
            build_records.append({
                "id": route["id"],
                "plannedPointCount": len(planned),
                "geometryRowsWritten": rows,
                "sourcePort": src_port,
                "targetPort": dst_port,
            })

        vsdx = os.path.join(OUT, "C4_1_Routing.vsdx")
        svg = os.path.join(OUT, "C4_1_Routing.raw.svg")
        png = os.path.join(OUT, "C4_1_Routing.png")
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
        with open(os.path.join(OUT, "C4_1-build-record.json"), "w", encoding="utf-8") as handle:
            json.dump({
                "status": "BUILT",
                "layoutRoutePassiveSet": route_passive_set,
                "connectorCount": len(build_records),
                "routes": build_records,
            }, handle, ensure_ascii=False, indent=2)
        return 0
    except Exception as exc:
        with open(os.path.join(OUT, "C4_1-build-record.json"), "w", encoding="utf-8") as handle:
            json.dump({"status": "FAIL", "error": repr(exc), "routes": build_records}, handle, ensure_ascii=False, indent=2)
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
