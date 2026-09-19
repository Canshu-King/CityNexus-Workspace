"""C4.1d: repair Visio row-index handling and realize explicit waypoints on native UML Associations.

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
VIS_TAG_MOVE_TO = 138
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


def snapshot_geometry_rows(connector) -> list[dict]:
    """Return an indexed snapshot of the persisted Geometry1 vertex rows."""
    row_count = int(connector.RowCount(VIS_SECTION_GEOMETRY_1))
    out = []
    for row in range(1, row_count):
        row_type = geometry_row_type(connector, row)
        rec = {"rowIndex": row, "rowType": row_type}
        try:
            rec["xIn"] = float(connector.CellsSRC(VIS_SECTION_GEOMETRY_1, row, VIS_X).Result("inches"))
            rec["yIn"] = float(connector.CellsSRC(VIS_SECTION_GEOMETRY_1, row, VIS_Y).Result("inches"))
        except Exception as exc:
            rec["readError"] = repr(exc)
        out.append(rec)
    return out


def write_geometry_after_glue(
    connector,
    logical_points,
    page_h_cm: float,
    diagnostics: dict | None = None,
) -> dict:
    """Install the planned polyline WITHOUT deleting native Geometry rows.

    C4.1b and C4.1c established an important local runtime behavior:
    deleting router-generated LineTo rows on a live glued Microsoft UML
    Association causes Visio to preserve/recreate route rows.  Therefore
    structural deletion is no longer part of the experiment.

    C4.1d uses a non-destructive strategy:

    1. inspect the currently persisted MoveTo/LineTo vertex rows;
    2. require no more existing vertex rows than planned route vertices;
    3. append any missing LineTo rows first, initially placing them at the
       final endpoint so the glued target remains geometrically represented;
    4. rewrite the complete existing row set in-place to the planned points;
    5. verify row count and row types never mutate unexpectedly.

    This tests whether Visio will preserve an explicit orthogonal polyline when
    only row values are rewritten and extra rows are appended, without any
    DeleteRow operation.
    """
    if len(logical_points) < 2:
        raise ValueError("route needs at least two points")

    diagnostics = diagnostics if diagnostics is not None else {}

    page_points = [logical_to_page_in(x, y, page_h_cm) for x, y in logical_points]
    local_points = [page_to_local(connector, x, y) for x, y in page_points]
    desired_vertex_count = len(local_points)

    pre_rows = snapshot_geometry_rows(connector)
    initial_row_count = int(connector.RowCount(VIS_SECTION_GEOMETRY_1))
    existing_vertex_count = initial_row_count - 1

    diagnostics["preRewriteRowCount"] = initial_row_count
    diagnostics["preRewriteRows"] = pre_rows
    diagnostics["plannedLogicalPoints"] = [list(map(float, p)) for p in logical_points]
    diagnostics["plannedLocalPointsIn"] = [list(map(float, p)) for p in local_points]
    diagnostics["desiredVertexCount"] = desired_vertex_count
    diagnostics["existingVertexCount"] = existing_vertex_count

    if initial_row_count < 3:
        raise RuntimeError(
            f"Geometry1 lacks the native MoveTo+LineTo minimum: rowCount={initial_row_count}"
        )

    initial_types = [geometry_row_type(connector, row) for row in range(1, initial_row_count)]
    if initial_types[0] != VIS_TAG_MOVE_TO:
        raise RuntimeError(
            f"Geometry1 row 1 is not MoveTo: actual={initial_types[0]}"
        )
    if any(t != VIS_TAG_LINE_TO for t in initial_types[1:]):
        raise RuntimeError(
            f"Geometry1 contains unexpected native row types: {initial_types}"
        )

    if existing_vertex_count > desired_vertex_count:
        raise RuntimeError(
            "router created more vertices than the approved planned route; "
            f"existing={existing_vertex_count}, planned={desired_vertex_count}. "
            "C4.1d intentionally does not delete rows."
        )

    # Append missing rows first.  Every newly-created row is temporarily placed
    # at the FINAL endpoint.  Thus the last geometry vertex remains the glued
    # target while the row set is being expanded.
    append_steps = []
    final_x, final_y = local_points[-1]
    while int(connector.RowCount(VIS_SECTION_GEOMETRY_1)) - 1 < desired_vertex_count:
        before = int(connector.RowCount(VIS_SECTION_GEOMETRY_1))
        ix = int(connector.AddRow(
            VIS_SECTION_GEOMETRY_1,
            VIS_ROW_LAST,
            VIS_TAG_LINE_TO,
        ))
        force(connector.CellsSRC(VIS_SECTION_GEOMETRY_1, ix, VIS_X), f"{final_x} in")
        force(connector.CellsSRC(VIS_SECTION_GEOMETRY_1, ix, VIS_Y), f"{final_y} in")
        after = int(connector.RowCount(VIS_SECTION_GEOMETRY_1))
        step = {
            "addedRowIndex": ix,
            "rowCountBefore": before,
            "rowCountAfter": after,
            "rowsAfterAdd": snapshot_geometry_rows(connector),
        }
        append_steps.append(step)
        if after != before + 1:
            diagnostics["appendSteps"] = append_steps
            raise RuntimeError(
                f"Geometry1 row count changed unexpectedly during AddRow: "
                f"before={before}, after={after}, addedRow={ix}"
            )

    diagnostics["appendSteps"] = append_steps
    expanded_row_count = int(connector.RowCount(VIS_SECTION_GEOMETRY_1))
    diagnostics["expandedRowCount"] = expanded_row_count
    diagnostics["expandedRows"] = snapshot_geometry_rows(connector)

    expected_row_count = desired_vertex_count + 1
    if expanded_row_count != expected_row_count:
        raise RuntimeError(
            f"Geometry1 expansion mismatch: actual={expanded_row_count}, "
            f"expected={expected_row_count}"
        )

    # Rewrite values in place.  No row structure changes from this point on.
    rewrite_steps = []
    for row, (local_x, local_y) in enumerate(local_points, start=1):
        before = int(connector.RowCount(VIS_SECTION_GEOMETRY_1))
        expected_type = VIS_TAG_MOVE_TO if row == 1 else VIS_TAG_LINE_TO
        actual_type = geometry_row_type(connector, row)
        if actual_type != expected_type:
            diagnostics["rewriteSteps"] = rewrite_steps
            raise RuntimeError(
                f"Geometry1 row type changed before rewrite at row {row}: "
                f"actual={actual_type}, expected={expected_type}"
            )

        force(connector.CellsSRC(VIS_SECTION_GEOMETRY_1, row, VIS_X), f"{local_x} in")
        force(connector.CellsSRC(VIS_SECTION_GEOMETRY_1, row, VIS_Y), f"{local_y} in")

        after = int(connector.RowCount(VIS_SECTION_GEOMETRY_1))
        step = {
            "rowIndex": row,
            "rowType": expected_type,
            "rowCountBefore": before,
            "rowCountAfter": after,
            "rowsAfterRewrite": snapshot_geometry_rows(connector),
        }
        rewrite_steps.append(step)
        if after != expected_row_count:
            diagnostics["rewriteSteps"] = rewrite_steps
            raise RuntimeError(
                f"Geometry1 structure changed during value rewrite at row {row}: "
                f"actualRowCount={after}, expected={expected_row_count}"
            )

    diagnostics["rewriteSteps"] = rewrite_steps

    final_count = int(connector.RowCount(VIS_SECTION_GEOMETRY_1))
    final_rows = snapshot_geometry_rows(connector)
    final_types = [geometry_row_type(connector, row) for row in range(1, final_count)]
    expected_types = [VIS_TAG_MOVE_TO] + [VIS_TAG_LINE_TO] * (desired_vertex_count - 1)

    diagnostics["finalGeometryRowCount"] = final_count
    diagnostics["finalGeometryRows"] = final_rows

    if final_count != expected_row_count:
        raise RuntimeError(
            f"Geometry1 final row count mismatch: actual={final_count}, expected={expected_row_count}"
        )
    if final_types != expected_types:
        raise RuntimeError(
            f"Geometry1 final row types mismatch: actual={final_types}, expected={expected_types}"
        )

    return {
        "strategy": "no-delete-expand-then-rewrite",
        "preGeometryRows": pre_rows,
        "initialVertexCount": existing_vertex_count,
        "plannedPointCount": desired_vertex_count,
        "appendSteps": append_steps,
        "rewriteSteps": rewrite_steps,
        "finalGeometryRows": final_rows,
    }


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
    page.NameU = "C4_1D_Routing"
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
    route_diagnostics = {}
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
            route_diagnostics[active_route] = {
                "preWriteGeometry": snapshot_geometry_rows(conn),
                "preWriteRowCount": int(conn.RowCount(VIS_SECTION_GEOMETRY_1)),
            }
            geometry_result = write_geometry_after_glue(
                conn,
                planned,
                page_h,
                route_diagnostics[active_route],
            )
            route_diagnostics[active_route]["postWriteGeometry"] = snapshot_geometry_rows(conn)
            route_diagnostics[active_route]["postWriteRowCount"] = int(conn.RowCount(VIS_SECTION_GEOMETRY_1))
            build_records.append({
                "id": route["id"],
                "plannedPointCount": len(planned),
                "geometryNormalization": geometry_result,
                "sourcePort": {k: v for k, v in src_port.items() if k not in ("xCell", "yCell")},
                "targetPort": {k: v for k, v in dst_port.items() if k not in ("xCell", "yCell")},
            })

        active_route = None
        stage = "save-export"
        vsdx = os.path.join(OUT, "C4_1D_Routing.vsdx")
        svg = os.path.join(OUT, "C4_1D_Routing.raw.svg")
        png = os.path.join(OUT, "C4_1D_Routing.png")
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
        with open(os.path.join(OUT, "C4_1D-build-record.json"), "w", encoding="utf-8") as handle:
            json.dump({
                "status": "BUILT",
                "layoutRoutePassiveSet": route_passive_set,
                "connectorCount": len(build_records),
                "routes": build_records,
                "routeDiagnostics": route_diagnostics,
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
            "routeDiagnostics": route_diagnostics,
        }
        with open(os.path.join(OUT, "C4_1D-build-record.json"), "w", encoding="utf-8") as handle:
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
