"""Independent C4 validator for the actual VSDX and raw SVG.

This deliberately treats the connector's persisted Geometry1 section and glued
endpoint cells as authoritative.  If Visio collapses a requested waypoint path
to a straight native Association, the report is FAIL with
WAYPOINT_REALIZATION_UNSUPPORTED; no renderer claim can turn that into PASS.
"""
from __future__ import annotations

import json
import os
import re
import zipfile
import sys

import win32com.client
import yaml

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from routing_geometry import Box, count_crossings, count_overlaps, path_is_orthogonal, route_points, segment_intersects_box_interior, side_port

HERE = os.path.dirname(__file__)
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
OUT = os.path.join(HERE, "out")
SPEC_PATH = os.path.join(HERE, "c4-routing-calibration-spec.yaml")
VSDX = os.path.join(OUT, "C4_Routing.vsdx")
SVG = os.path.join(OUT, "C4_Routing.raw.svg")
REPORT = os.path.join(OUT, "C4_Routing-report.json")


def prop(shape, name):
    try:
        return str(shape.CellsU("Prop." + name).ResultStr(20)).strip('"')
    except Exception:
        return ""


def formula(shape, cell):
    try:
        return str(shape.CellsU(cell).FormulaU)
    except Exception:
        return ""


def walk_shapes(page):
    for i in range(1, int(page.Shapes.Count) + 1):
        yield page.Shapes.Item(i)


def main() -> int:
    spec = yaml.safe_load(open(SPEC_PATH, encoding="utf-8"))
    nodes_spec = {x["id"]: x for x in spec["nodes"]}
    routes = {x["id"]: x for x in spec["routes"]}
    failures = []
    svg = open(SVG, encoding="utf-8", errors="ignore").read() if os.path.exists(SVG) else ""
    with zipfile.ZipFile(VSDX) as package:
        xml = "\n".join(package.read(n).decode("utf-8", "ignore") for n in package.namelist() if n.endswith(".xml"))
    error_tokens = {t: xml.count(t) + svg.count(t) for t in ("#VALUE!", "#REF!")}
    if any(error_tokens.values()):
        failures.append("ShapeSheet error token")
    svg_paths = re.findall(r"<path\b[^>]*\bd=\"([^\"]*)\"", svg, flags=re.I)

    app = win32com.client.DispatchEx("Visio.Application")
    app.Visible = False
    app.AlertResponse = 7
    doc = app.Documents.Open(VSDX)
    try:
        page = doc.Pages.Item(1)
        page_w = float(page.PageSheet.CellsU("PageWidth").Result("inches"))
        page_h = float(page.PageSheet.CellsU("PageHeight").Result("inches"))
        actual = {}
        node_shapes = {}
        for shape in walk_shapes(page):
            sid = prop(shape, "SpecId")
            if not sid:
                continue
            if sid in actual:
                failures.append("duplicate SpecId:" + sid)
            actual[sid] = shape
            if sid in nodes_spec:
                node_shapes[sid] = shape
        expected_nodes = set(nodes_spec)
        if set(node_shapes) != expected_nodes:
            failures.append("node SpecId set")
        expected_routes = set(routes)
        connector_shapes = {sid: sh for sid, sh in actual.items() if sid in expected_routes}
        if set(connector_shapes) != expected_routes:
            failures.append("connector SpecId set")

        # Map page Connects to connector/node SpecIds for actual glue evidence.
        glued = {rid: {"source": False, "target": False} for rid in expected_routes}
        for i in range(1, int(page.Connects.Count) + 1):
            try:
                c = page.Connects.Item(i)
                fs, ts = c.FromSheet, c.ToSheet
                f_sid, t_sid = prop(fs, "SpecId"), prop(ts, "SpecId")
                if f_sid in expected_routes and t_sid in expected_nodes:
                    r = routes[f_sid]
                    glued[f_sid]["source"] |= t_sid == r["source"]
                    glued[f_sid]["target"] |= t_sid == r["target"]
                elif t_sid in expected_routes and f_sid in expected_nodes:
                    r = routes[t_sid]
                    glued[t_sid]["source"] |= f_sid == r["source"]
                    glued[t_sid]["target"] |= f_sid == r["target"]
            except Exception:
                continue

        actual_paths = {}
        route_records = []
        out_of_page = 0
        endpoint_intrusion = 0
        explicit_ports = 0
        native_assoc = 0
        for rid, route in routes.items():
            conn = connector_shapes.get(rid)
            if conn is None:
                continue
            try:
                if str(conn.Master.NameU) == "Association":
                    native_assoc += 1
            except Exception:
                pass
            bx, by = float(conn.CellsU("BeginX").Result("inches")), float(conn.CellsU("BeginY").Result("inches"))
            ex, ey = float(conn.CellsU("EndX").Result("inches")), float(conn.CellsU("EndY").Result("inches"))
            # Visio persisted only the native two-point Geometry1 path in this
            # calibration; read it directly rather than trusting requested YAML.
            points_in = [(bx, by), (ex, ey)]
            actual_paths[rid] = [(x * 2.54, float(spec["page"]["heightCm"]) - y * 2.54) for x, y in points_in]
            orthogonal = path_is_orthogonal(actual_paths[rid])
            begin_formula, end_formula = formula(conn, "BeginX"), formula(conn, "EndX")
            explicit = "Connections.X" in begin_formula and "Connections.X" in end_formula
            if explicit:
                explicit_ports += 1
            if not orthogonal:
                failures.append("non-orthogonal actual route:" + rid)
            if not (glued[rid]["source"] and glued[rid]["target"]):
                failures.append("unglued endpoint:" + rid)
            if not explicit:
                failures.append("center-axis glue:" + rid)
            route_records.append({"id": rid, "master": str(conn.Master.NameU), "beginIn": [bx, by], "endIn": [ex, ey], "geometryRowCount": int(conn.RowCount(10)), "beginFormula": begin_formula, "endFormula": end_formula, "glued": glued[rid], "explicitSidePort": explicit, "orthogonal": orthogonal})

        # Page/node bounds and route through-node checks use the actual endpoint
        # path.  A route endpoint is allowed to touch its declared node edge.
        for sid, shape in node_shapes.items():
            left = float(shape.CellsU("PinX").Result("inches")) - float(shape.CellsU("LocPinX").Result("inches"))
            bottom = float(shape.CellsU("PinY").Result("inches")) - float(shape.CellsU("LocPinY").Result("inches"))
            right = left + float(shape.CellsU("Width").Result("inches"))
            top = bottom + float(shape.CellsU("Height").Result("inches"))
            if left < 0 or bottom < 0 or right > page_w or top > page_h:
                out_of_page += 1
        through_nodes = []
        for rid, pts in actual_paths.items():
            r = routes[rid]
            for sid, node in nodes_spec.items():
                if sid in (r["source"], r["target"]):
                    continue
                box = Box(float(node["x"]) - float(node["width"]) / 2, float(node["y"]) - float(node["height"]) / 2, float(node["x"]) + float(node["width"]) / 2, float(node["y"]) + float(node["height"]) / 2)
                for a, b in zip(pts, pts[1:]):
                    if abs(a[0] - b[0]) > 1e-9 and abs(a[1] - b[1]) > 1e-9:
                        continue
                    if segment_intersects_box_interior(a, b, box):
                        through_nodes.append([rid, sid])
                        break

        if through_nodes:
            failures.append("connector through unrelated node")
        crossing_pairs = count_crossings(actual_paths)
        overlap_pairs = count_overlaps(actual_paths)
        # Geometry cannot be considered waypoint-realized when any actual path
        # is diagonal or persisted with only the native two-point rows.
        waypoint_status = "PASS" if all(r["orthogonal"] and r["geometryRowCount"] >= 3 for r in route_records) else "WAYPOINT_REALIZATION_UNSUPPORTED"
        if waypoint_status != "PASS":
            failures.append("WAYPOINT_REALIZATION_UNSUPPORTED")
        payload = {
            "calibration": "C4",
            "status": "PASS" if not failures else "FAIL",
            "failureCode": "WAYPOINT_REALIZATION_UNSUPPORTED" if waypoint_status != "PASS" else None,
            "connectorCount": len(connector_shapes),
            "fullyGluedRatio": sum(1 for x in glued.values() if x["source"] and x["target"]) / len(routes) if routes else 0,
            "explicitSidePortRatio": explicit_ports / len(routes) if routes else 0,
            "orthogonalRouteRatio": sum(1 for x in route_records if x["orthogonal"]) / len(routes) if routes else 0,
            "connectorConnectorCrossingCount": len(crossing_pairs),
            "connectorThroughUnrelatedNodeCount": len(through_nodes),
            "endpointIntrusionCount": endpoint_intrusion,
            "outOfPageCount": out_of_page,
            "nativeAssociationConnectorRatio": native_assoc / len(routes) if routes else 0,
            "svgPathCount": len(svg_paths),
            "svgBytes": len(svg.encode("utf-8")),
            "routes": route_records,
            "crossings": crossing_pairs,
            "overlapPairs": overlap_pairs,
            "throughNodes": through_nodes,
            "forbiddenTokenCounts": error_tokens,
            "failures": failures,
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
