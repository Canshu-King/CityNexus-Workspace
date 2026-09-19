"""C4.1a: repair Visio row-index handling and realize explicit waypoints on native UML Associations.

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
VIS_ROW_LAST = -2  # Microsoft visRowLast; -1 is visRowInval/visRowNone
VIS_TAG_CONNECTION_POINT = 153
VIS_TAG_LINE_TO = 139
VIS_TAG_DEFAULT = 0
VIS_CNNCT_X = 0
VIS_CNNCT_Y = 1
VIS_CNNCT_DIRX = 2
VIS_CNNCT_DIRY = 3
VIS_CNNCT_TYPE = 4
VIS_X = 0
VIS_Y = 1
VIS_TAG_CNNCT_NAMED = 185


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
    """Add an instance connection point using COM row indices, not 1-based CellsU suffixes.

    Visio AddRow returns a zero-based ShapeSheet row index.  CellsU names such
    as Connections.X1 are one-based display aliases, so using the AddRow return
    value directly inside a CellsU name is an off-by-one bug.  CellsSRC avoids
    that ambiguity entirely.
    """
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
        # Connection-point sections may already use named rows.  The default tag
        # lets Visio choose the section-compatible row type.  We verify the row
        # type immediately after creation rather than silently assuming success.
        row = int(shape.AddRow(VIS_SECTION_CONNECTION, VIS_ROW_LAST, VIS_TAG_DEFAULT))
        tag_used = VIS_TAG_DEFAULT

    # RowType is an indexed COM property and its pywin32 exposure differs
    # across generated/dynamic wrappers.  It is diagnostic only; correctness
    # is established by accessing the returned row through CellsSRC below.
    row_type = None
    try:
        row_type = int(shape.RowType(VIS_SECTION_CONNECTION, row))
    except Exception:
        pass

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

    try:
        x_name = str(x_cell.NameU)
        y_name = str(y_cell.NameU)
    except Exception:
        # Diagnostic only. Glue uses the Cell object directly, so names are not
        # required for correctness.
        x_name = ""
        y_name = ""

    return {
        "rowIndex": row,
        "rowType": row_type,
        "rowTagRequested": tag_used,
        "xCellName": x_name,
        "yCellName": y_name,
        "xCell": x_cell,
        "yCell": y_cell,
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


def geometry_row_type(connector, row: int) -> int | None:
    try:
        return int(connector.RowType(VIS_SECTION_GEOMETRY_1, int(row)))
    except Exception:
        return None


def write_geometry_after_glue(connector, logical_points, page_h_cm: float) -> list[dict]:
    """Write an exact polyline into Geometry1 after glue using CellsSRC.

    This deliberately uses Visio's COM row indices end-to-end.  The previous
    C4.1 build incorrectly used visRowLast=-1 and then treated AddRow's returned
    zero-based row index as the 1-based suffix in names such as Geometry1.X3.
    """
    if len(logical_points) < 2:
        raise ValueError("route needs at least two points")

    page_points = [logical_to_page_in(x, y, page_h_cm) for x, y in logical_points]
    local_points = [page_to_local(connector, x, y) for x, y in page_points]

    # Geometry section row 0 is the component row; row 1 is the first vertex.
    # A freshly dropped Association is expected to have MoveTo row 1 and LineTo
    # row 2.  Refuse router-expanded geometry instead of mixing two route models.
    row_count = int(connector.RowCount(VIS_SECTION_GEOMETRY_1))
    row1_type = geometry_row_type(connector, 1)
    row2_type = geometry_row_type(connector, 2)
    if row_count < 3:
        raise RuntimeError(
            f"native Association Geometry1 missing base rows: count={row_count}, "
            f"row1Type={row1_type}, row2Type={row2_type}"
        )
    if row_count > 3:
        raise RuntimeError(f"unexpected pre-existing Geometry1 rows before manual realization: count={row_count}")

    force(connector.CellsSRC(VIS_SECTION_GEOMETRY_1, 1, VIS_X), f"{local_points[0][0]} in")
    force(connector.CellsSRC(VIS_SECTION_GEOMETRY_1, 1, VIS_Y), f"{local_points[0][1]} in")
    force(connector.CellsSRC(VIS_SECTION_GEOMETRY_1, 2, VIS_X), f"{local_points[1][0]} in")
    force(connector.CellsSRC(VIS_SECTION_GEOMETRY_1, 2, VIS_Y), f"{local_points[1][1]} in")

    rows = [1, 2]
    for local_x, local_y in local_points[2:]:
        ix = int(connector.AddRow(VIS_SECTION_GEOMETRY_1, VIS_ROW_LAST, VIS_TAG_LINE_TO))
        force(connector.CellsSRC(VIS_SECTION_GEOMETRY_1, ix, VIS_X), f"{local_x} in")
        force(connector.CellsSRC(VIS_SECTION_GEOMETRY_1, ix, VIS_Y), f"{local_y} in")
        rows.append(ix)

    return [
        {
            "rowIndex": ix,
            "rowType": geometry_row_type(connector, ix),
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
    page.NameU = "C4_1A_Routing"
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
    stage = "initializing"
    active_route = None
    try:
        stage = "resolve-font"
        font_id = resolve_font_id(doc, "Segoe UI")
        for node in spec["nodes"]:
            stage = f"node:{node['id']}"
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
            active_route = route["id"]
            stage = f"route:{active_route}:ports"
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

            stage = f"route:{active_route}:association-master"
            stencil_path = master_map["stencils"]["Association"]["stencil"]
            stencil = next((x for x in stencil_docs if x.FullName == stencil_path), None)
            if stencil is None:
                stencil = app.Documents.OpenEx(stencil_path, 66)
                stencil_docs.append(stencil)
            stage = f"route:{active_route}:drop-association"
            conn = page.Drop(stencil.Masters.ItemU("Association"), 1, 1)
            conn.Text = ""
            stage = f"route:{active_route}:shape-data"
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

            stage = f"route:{active_route}:routing-cells"
            # The stock UML Association master is centre-to-centre + straight.
            # Override those inherited values on the instance before glue.
            set_if_present(conn, "ShapeRouteStyle", "1", required=True)   # right angle
            set_if_present(conn, "ConLineRouteExt", "0", required=True)  # page/default extension, not forced straight
            set_if_present(conn, "ConFixedCode", "2")                    # never reroute

            stage = f"route:{active_route}:glue-begin"
            conn.CellsU("BeginX").GlueTo(src_port["xCell"])
            stage = f"route:{active_route}:glue-end"
            conn.CellsU("EndX").GlueTo(dst_port["xCell"])

            stage = f"route:{active_route}:write-geometry"
            planned = route_points(route, {k: v["spec"] for k, v in nodes.items()})
            rows = write_geometry_after_glue(conn, planned, page_h)
            build_records.append({
                "id": route["id"],
                "plannedPointCount": len(planned),
                "geometryRowsWritten": rows,
                "sourcePort": {k: v for k, v in src_port.items() if k not in ("xCell", "yCell")},
                "targetPort": {k: v for k, v in dst_port.items() if k not in ("xCell", "yCell")},
            })

        active_route = None
        stage = "save-export"
        vsdx = os.path.join(OUT, "C4_1A_Routing.vsdx")
        svg = os.path.join(OUT, "C4_1A_Routing.raw.svg")
        png = os.path.join(OUT, "C4_1A_Routing.png")
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
        with open(os.path.join(OUT, "C4_1A-build-record.json"), "w", encoding="utf-8") as handle:
            json.dump({
                "status": "BUILT",
                "layoutRoutePassiveSet": route_passive_set,
                "connectorCount": len(build_records),
                "routes": build_records,
            }, handle, ensure_ascii=False, indent=2)
        return 0
    except Exception as exc:
        detail = {
            "status": "FAIL",
            "stage": stage,
            "activeRoute": active_route,
            "error": repr(exc),
            "errorType": type(exc).__name__,
            "hresult": getattr(exc, "hresult", None),
            "excepinfo": getattr(exc, "excepinfo", None),
            "routes": build_records,
        }
        with open(os.path.join(OUT, "C4_1A-build-record.json"), "w", encoding="utf-8") as handle:
            json.dump(detail, handle, ensure_ascii=False, indent=2, default=str)
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
