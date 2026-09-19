"""Independent validator for the C4.1d native-Association waypoint repair experiment."""
from __future__ import annotations

import json
import math
import os
import re
import sys
import zipfile

import win32com.client
import yaml

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from routing_geometry import (  # noqa: E402
    Box,
    count_crossings,
    count_overlaps,
    path_is_orthogonal,
    route_points,
    segment_intersects_box_interior,
)

HERE = os.path.dirname(__file__)
OUT = os.path.join(HERE, "out")
SPEC_PATH = os.path.join(HERE, "c4-routing-calibration-spec.yaml")
VSDX = os.path.join(OUT, "C4_1D_Routing.vsdx")
SVG = os.path.join(OUT, "C4_1D_Routing.raw.svg")
REPORT = os.path.join(OUT, "C4_1D_Routing-report.json")
TOL_CM = 0.05  # 0.5 mm

VIS_SECTION_GEOMETRY_1 = 10
VIS_X = 0
VIS_Y = 1
VIS_TAG_MOVE_TO = 138
VIS_TAG_LINE_TO = 139


def prop(shape, name: str) -> str:
    try:
        return str(shape.CellsU("Prop." + name).ResultStr(20)).strip('"')
    except Exception:
        return ""


def formula(shape, name: str) -> str:
    try:
        return str(shape.CellsU(name).FormulaU)
    except Exception:
        return ""


def cell_result(shape, name: str, unit: str = "inches") -> float:
    return float(shape.CellsU(name).Result(unit))


def local_to_page(conn, x: float, y: float) -> tuple[float, float]:
    pin_x = cell_result(conn, "PinX")
    pin_y = cell_result(conn, "PinY")
    loc_x = cell_result(conn, "LocPinX")
    loc_y = cell_result(conn, "LocPinY")
    angle = cell_result(conn, "Angle", "radians")
    dx, dy = x - loc_x, y - loc_y
    c, s = math.cos(angle), math.sin(angle)
    return pin_x + c * dx - s * dy, pin_y + s * dx + c * dy


def geometry_local_points(conn, max_rows: int = 128):
    """Read Geometry1 through COM row indices and return points + row metadata."""
    try:
        count = int(conn.RowCount(VIS_SECTION_GEOMETRY_1))
    except Exception:
        return [], []

    pts = []
    rows = []
    for row in range(1, min(count, max_rows)):
        try:
            row_type = int(conn.RowType(VIS_SECTION_GEOMETRY_1, row))
        except Exception:
            row_type = None
        rec = {"rowIndex": row, "rowType": row_type}
        try:
            x = float(conn.CellsSRC(VIS_SECTION_GEOMETRY_1, row, VIS_X).Result("inches"))
            y = float(conn.CellsSRC(VIS_SECTION_GEOMETRY_1, row, VIS_Y).Result("inches"))
            rec["localIn"] = [x, y]
            if row_type in (VIS_TAG_MOVE_TO, VIS_TAG_LINE_TO):
                pts.append((x, y))
        except Exception as exc:
            rec["readError"] = repr(exc)
        rows.append(rec)
    return pts, rows


def compact(points, eps: float = 1e-8):
    out = []
    for p in points:
        if not out or abs(p[0]-out[-1][0]) > eps or abs(p[1]-out[-1][1]) > eps:
            out.append(p)
    return out


def max_point_delta_cm(actual, expected) -> float | None:
    if len(actual) != len(expected):
        return None
    return max((math.hypot(a[0]-e[0], a[1]-e[1]) for a, e in zip(actual, expected)), default=0.0)


def main() -> int:
    with open(SPEC_PATH, encoding="utf-8") as handle:
        spec = yaml.safe_load(handle)
    page_h_cm = float(spec["page"]["heightCm"])
    nodes_spec = {x["id"]: x for x in spec["nodes"]}
    routes = {x["id"]: x for x in spec["routes"]}
    failures = []

    if not os.path.exists(VSDX) or not os.path.exists(SVG):
        payload = {"calibration": "C4.1d", "status": "FAIL", "failures": ["missing C4.1d artifacts"]}
        with open(REPORT, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2)
        return 1

    svg = open(SVG, encoding="utf-8", errors="ignore").read()
    with zipfile.ZipFile(VSDX) as zf:
        xml = "\n".join(zf.read(n).decode("utf-8", "ignore") for n in zf.namelist() if n.endswith(".xml"))
    error_tokens = {t: xml.count(t) + svg.count(t) for t in ("#VALUE!", "#REF!", "#NAME?")}
    if any(error_tokens.values()):
        failures.append("ShapeSheet error token")

    app = win32com.client.DispatchEx("Visio.Application")
    app.Visible = False
    app.AlertResponse = 7
    doc = app.Documents.Open(VSDX)
    try:
        page = doc.Pages.Item(1)
        page_w = float(page.PageSheet.CellsU("PageWidth").Result("inches"))
        page_h = float(page.PageSheet.CellsU("PageHeight").Result("inches"))
        actual = {}
        for i in range(1, int(page.Shapes.Count)+1):
            sh = page.Shapes.Item(i)
            sid = prop(sh, "SpecId")
            if sid:
                if sid in actual:
                    failures.append("duplicate SpecId:" + sid)
                actual[sid] = sh

        node_shapes = {sid: actual[sid] for sid in nodes_spec if sid in actual}
        conn_shapes = {rid: actual[rid] for rid in routes if rid in actual}
        if set(node_shapes) != set(nodes_spec): failures.append("node SpecId set")
        if set(conn_shapes) != set(routes): failures.append("connector SpecId set")

        node_geometry = []
        for sid, node in nodes_spec.items():
            sh = node_shapes.get(sid)
            if sh is None:
                continue
            pin_x = cell_result(sh, "PinX")
            pin_y = cell_result(sh, "PinY")
            width = cell_result(sh, "Width")
            height = cell_result(sh, "Height")
            actual_x_cm = pin_x * 2.54
            actual_y_cm = page_h_cm - pin_y * 2.54
            rec = {
                "id": sid,
                "actualCenterCm": [actual_x_cm, actual_y_cm],
                "expectedCenterCm": [float(node["x"]), float(node["y"])],
                "actualSizeCm": [width*2.54, height*2.54],
                "expectedSizeCm": [float(node["width"]), float(node["height"])],
            }
            rec["maxGeometryDeltaCm"] = max(
                abs(actual_x_cm-float(node["x"])),
                abs(actual_y_cm-float(node["y"])),
                abs(width*2.54-float(node["width"])),
                abs(height*2.54-float(node["height"])),
            )
            rec["match"] = rec["maxGeometryDeltaCm"] <= TOL_CM
            if not rec["match"]:
                failures.append("node geometry mismatch:"+sid)
            node_geometry.append(rec)

        glued = {rid: {"source": False, "target": False} for rid in routes}
        for i in range(1, int(page.Connects.Count)+1):
            try:
                c = page.Connects.Item(i)
                fs, ts = c.FromSheet, c.ToSheet
                f_sid, t_sid = prop(fs, "SpecId"), prop(ts, "SpecId")
                if f_sid in routes and t_sid in nodes_spec:
                    glued[f_sid]["source"] |= t_sid == routes[f_sid]["source"]
                    glued[f_sid]["target"] |= t_sid == routes[f_sid]["target"]
                elif t_sid in routes and f_sid in nodes_spec:
                    glued[t_sid]["source"] |= f_sid == routes[t_sid]["source"]
                    glued[t_sid]["target"] |= f_sid == routes[t_sid]["target"]
            except Exception:
                pass

        actual_paths = {}
        records = []
        native_assoc = 0
        explicit_ports = 0
        waypoint_matches = 0
        directional_ports = 0

        for rid, route in routes.items():
            conn = conn_shapes.get(rid)
            if conn is None:
                continue
            try:
                if str(conn.Master.NameU) == "Association": native_assoc += 1
            except Exception:
                pass
            bf, ef = formula(conn, "BeginX"), formula(conn, "EndX")
            explicit = "Connections.X" in bf and "Connections.X" in ef
            explicit_ports += int(explicit)

            local, geometry_rows = geometry_local_points(conn)
            page_pts_in = [local_to_page(conn, x, y) for x, y in local]
            logical = compact([(x*2.54, page_h_cm-y*2.54) for x, y in page_pts_in])
            actual_paths[rid] = logical
            expected = route_points(route, nodes_spec)
            delta = max_point_delta_cm(logical, expected)
            waypoint_match = delta is not None and delta <= TOL_CM
            waypoint_matches += int(waypoint_match)
            orthogonal = path_is_orthogonal(logical)
            begin_logical = (cell_result(conn, "BeginX")*2.54, page_h_cm-cell_result(conn, "BeginY")*2.54)
            end_logical = (cell_result(conn, "EndX")*2.54, page_h_cm-cell_result(conn, "EndY")*2.54)
            endpoint_geometry_error = None
            endpoint_geometry_aligned = False
            if logical:
                endpoint_geometry_error = max(
                    math.hypot(logical[0][0]-begin_logical[0], logical[0][1]-begin_logical[1]),
                    math.hypot(logical[-1][0]-end_logical[0], logical[-1][1]-end_logical[1]),
                )
                endpoint_geometry_aligned = endpoint_geometry_error <= TOL_CM

            # Verify the source/target instance ports have the requested outward direction.
            dir_ok = True
            for endpoint, sid, side, frac in (
                ("source", route["source"], route["sourceSide"], route["sourcePortFraction"]),
                ("target", route["target"], route["targetSide"], route["targetPortFraction"]),
            ):
                sh = node_shapes.get(sid)
                cell_formula = bf if endpoint == "source" else ef
                m = re.search(r"Connections\.X(\d+)", cell_formula)
                if not sh or not m:
                    dir_ok = False
                    continue
                ix = int(m.group(1))
                try:
                    dx = float(sh.CellsU(f"Connections.DirX{ix}").Result("") )
                    dy = float(sh.CellsU(f"Connections.DirY{ix}").Result("") )
                except Exception:
                    dir_ok = False
                    continue
                want = {"LEFT":(-1,0),"RIGHT":(1,0),"TOP":(0,1),"BOTTOM":(0,-1)}[side]
                if abs(dx-want[0]) > 1e-6 or abs(dy-want[1]) > 1e-6:
                    dir_ok = False
            directional_ports += int(dir_ok)

            expected_types = [VIS_TAG_MOVE_TO] + [VIS_TAG_LINE_TO] * max(0, len(expected) - 1)
            actual_types = [r.get("rowType") for r in geometry_rows]
            geometry_row_types_valid = actual_types == expected_types
            if not geometry_row_types_valid:
                failures.append("geometry row types/count mismatch:" + rid)

            if not orthogonal: failures.append("non-orthogonal:" + rid)
            if not waypoint_match: failures.append("waypoint mismatch:" + rid)
            if not (glued[rid]["source"] and glued[rid]["target"]): failures.append("unglued:" + rid)
            if not explicit: failures.append("not explicit side port:" + rid)
            if not dir_ok: failures.append("connection-point direction mismatch:" + rid)
            if not endpoint_geometry_aligned: failures.append("geometry endpoint detached from glue:" + rid)

            records.append({
                "id": rid,
                "master": str(conn.Master.NameU) if conn.Master else None,
                "geometryVertexCount": len(logical),
                "expectedVertexCount": len(expected),
                "geometryRows": geometry_rows,
                "geometryRowTypesValid": geometry_row_types_valid,
                "actualLogicalCm": logical,
                "expectedLogicalCm": expected,
                "maxPointDeltaCm": delta,
                "waypointMatch": waypoint_match,
                "orthogonal": orthogonal,
                "glued": glued[rid],
                "beginFormula": bf,
                "endFormula": ef,
                "explicitSidePort": explicit,
                "directionalPorts": dir_ok,
                "beginLogicalCm": begin_logical,
                "endLogicalCm": end_logical,
                "endpointGeometryDeltaCm": endpoint_geometry_error,
                "endpointGeometryAligned": endpoint_geometry_aligned,
                "ShapeRouteStyle": formula(conn, "ShapeRouteStyle"),
                "ConLineRouteExt": formula(conn, "ConLineRouteExt"),
                "ConFixedCode": formula(conn, "ConFixedCode"),
            })

        crossing_pairs = count_crossings(actual_paths)
        overlap_pairs = count_overlaps(actual_paths)
        through = []
        for rid, pts in actual_paths.items():
            route = routes[rid]
            for sid, node in nodes_spec.items():
                if sid in (route["source"], route["target"]):
                    continue
                box = Box(float(node["x"])-float(node["width"])/2, float(node["y"])-float(node["height"])/2,
                          float(node["x"])+float(node["width"])/2, float(node["y"])+float(node["height"])/2)
                if any(segment_intersects_box_interior(a,b,box) for a,b in zip(pts,pts[1:]) if abs(a[0]-b[0])<1e-9 or abs(a[1]-b[1])<1e-9):
                    through.append([rid,sid])

        out_of_page = 0
        for sid, sh in node_shapes.items():
            left = cell_result(sh,"PinX")-cell_result(sh,"LocPinX")
            bottom = cell_result(sh,"PinY")-cell_result(sh,"LocPinY")
            right = left+cell_result(sh,"Width")
            top = bottom+cell_result(sh,"Height")
            if left < 0 or bottom < 0 or right > page_w or top > page_h: out_of_page += 1
        for rid, pts in actual_paths.items():
            for x_cm,y_cm in pts:
                x,y=x_cm/2.54,(page_h_cm-y_cm)/2.54
                if x < -1e-6 or y < -1e-6 or x > page_w+1e-6 or y > page_h+1e-6:
                    out_of_page += 1
                    break

        if crossing_pairs: failures.append("connector crossing")
        if overlap_pairs: failures.append("connector overlap")
        if through: failures.append("connector through unrelated node")
        if out_of_page: failures.append("out of page")

        n = len(routes) or 1
        payload = {
            "calibration": "C4.1d",
            "status": "PASS" if not failures else "FAIL",
            "connectorCount": len(conn_shapes),
            "fullyGluedRatio": sum(1 for g in glued.values() if g["source"] and g["target"])/n,
            "explicitSidePortRatio": explicit_ports/n,
            "directionalSidePortRatio": directional_ports/n,
            "nativeAssociationConnectorRatio": native_assoc/n,
            "orthogonalRouteRatio": sum(1 for r in records if r["orthogonal"])/n,
            "manualWaypointMatchRatio": waypoint_matches/n,
            "connectorConnectorCrossingCount": len(crossing_pairs),
            "connectorOverlapPairCount": len(overlap_pairs),
            "connectorThroughUnrelatedNodeCount": len(through),
            "outOfPageCount": out_of_page,
            "forbiddenTokenCounts": error_tokens,
            "nodes": node_geometry,
            "routes": records,
            "crossings": crossing_pairs,
            "overlapPairs": overlap_pairs,
            "throughNodes": through,
            "failures": sorted(set(failures)),
        }
    finally:
        try:
            doc.Saved = True
            doc.Close()
        except Exception:
            pass
        try:
            app.Quit()
        except Exception:
            pass

    with open(REPORT, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
    print(json.dumps(payload, ensure_ascii=True, indent=2))
    return 0 if payload["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
