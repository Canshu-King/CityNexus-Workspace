"""Independent validator for the C4 semantic-native + presentation-route fallback."""
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
VSDX = os.path.join(OUT, "C4F_SemanticOverlay.vsdx")
SVG = os.path.join(OUT, "C4F_SemanticOverlay.raw.svg")
REPORT = os.path.join(OUT, "C4F_SemanticOverlay-report.json")

TOL_CM = 0.05  # 0.5 mm

VIS_SECTION_CONNECTION = 7
VIS_CNNCT_DIRX = 2
VIS_CNNCT_DIRY = 3


def prop(shape, name: str) -> str | None:
    try:
        if not int(shape.CellExistsU("Prop." + name, 0)):
            return None
        value = str(shape.CellsU("Prop." + name).ResultStr(""))
        return value.strip()
    except Exception:
        try:
            formula = str(shape.CellsU("Prop." + name).FormulaU)
            if formula.startswith('"') and formula.endswith('"'):
                return formula[1:-1].replace('""', '"')
            return formula
        except Exception:
            return None


def formula(shape, name: str) -> str:
    try:
        return str(shape.CellsU(name).FormulaU)
    except Exception:
        return ""


def cell_result(shape, name: str, units: str = "inches") -> float:
    return float(shape.CellsU(name).Result(units))


def logical_endpoint(shape, which: str, page_h_cm: float) -> tuple[float, float]:
    x = cell_result(shape, which + "X") * 2.54
    y = page_h_cm - cell_result(shape, which + "Y") * 2.54
    return (x, y)


def point_error(a, b) -> float:
    return math.hypot(float(a[0]) - float(b[0]), float(a[1]) - float(b[1]))


def colour_formula_ok(formula_u: str, rgb: tuple[int, int, int]) -> bool:
    compact = re.sub(r"\s+", "", str(formula_u)).upper()
    want = f"RGB({rgb[0]},{rgb[1]},{rgb[2]})"
    return compact == want



def connection_direction_from_endpoint_formula(shape, endpoint_formula: str) -> dict:
    """Read DirX/DirY for the exact connection-point row referenced by glue.

    A glued endpoint formula uses the display alias `Connections.XN`, where N
    is one-based.  CellsSRC uses the ShapeSheet row index, which is zero-based
    for the Connection Points section.  Therefore:

        Connections.X1 -> row index 0
        Connections.X2 -> row index 1
        ...

    Reading `Connections.DirXN` with CellsU is not reliable for this local
    Visio stencil and produced the false-negative C4F report.  Use CellsSRC on
    the actual indexed row instead.
    """
    match = re.search(r"Connections\.X(\d+)", str(endpoint_formula))
    if match is None:
        raise ValueError(f"endpoint is not glued to an explicit Connections.XN row: {endpoint_formula}")

    alias_index = int(match.group(1))
    if alias_index < 1:
        raise ValueError(f"invalid Connections.X alias index: {alias_index}")

    row_index = alias_index - 1
    dx = float(shape.CellsSRC(
        VIS_SECTION_CONNECTION,
        row_index,
        VIS_CNNCT_DIRX,
    ).Result(""))
    dy = float(shape.CellsSRC(
        VIS_SECTION_CONNECTION,
        row_index,
        VIS_CNNCT_DIRY,
    ).Result(""))

    return {
        "aliasIndex": alias_index,
        "rowIndex": row_index,
        "dirX": dx,
        "dirY": dy,
    }


def main() -> int:
    with open(SPEC_PATH, encoding="utf-8") as handle:
        spec = yaml.safe_load(handle)

    page_h_cm = float(spec["page"]["heightCm"])
    page_w_cm = float(spec["page"]["widthCm"])
    nodes_spec = {x["id"]: x for x in spec["nodes"]}
    routes = {x["id"]: x for x in spec["routes"]}

    failures = []

    if not os.path.exists(VSDX) or not os.path.exists(SVG):
        payload = {
            "calibration": "C4F",
            "status": "FAIL",
            "failures": ["missing fallback artifacts"],
        }
        with open(REPORT, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2)
        return 1

    svg = open(SVG, encoding="utf-8", errors="ignore").read()
    with zipfile.ZipFile(VSDX) as zf:
        xml = "\n".join(
            zf.read(n).decode("utf-8", "ignore")
            for n in zf.namelist()
            if n.endswith(".xml")
        )
    error_tokens = {t: xml.count(t) + svg.count(t) for t in ("#VALUE!", "#REF!", "#NAME?")}
    if any(error_tokens.values()):
        failures.append("ShapeSheet error token")

    app = win32com.client.DispatchEx("Visio.Application")
    app.Visible = False
    app.AlertResponse = 7
    doc = app.Documents.Open(VSDX)

    try:
        page = doc.Pages.Item(1)
        page_w_in = float(page.PageSheet.CellsU("PageWidth").Result("inches"))
        page_h_in = float(page.PageSheet.CellsU("PageHeight").Result("inches"))

        shapes = []
        by_spec = {}
        for i in range(1, int(page.Shapes.Count) + 1):
            sh = page.Shapes.Item(i)
            shapes.append(sh)
            sid = prop(sh, "SpecId")
            if sid:
                if sid in by_spec:
                    failures.append("duplicate SpecId:" + sid)
                by_spec[sid] = sh

        # Native nodes
        node_records = []
        for sid, node in nodes_spec.items():
            sh = by_spec.get(sid)
            if sh is None:
                failures.append("missing node:" + sid)
                continue

            x = cell_result(sh, "PinX") * 2.54
            y = page_h_cm - cell_result(sh, "PinY") * 2.54
            w = cell_result(sh, "Width") * 2.54
            h = cell_result(sh, "Height") * 2.54
            delta = max(
                abs(x - float(node["x"])),
                abs(y - float(node["y"])),
                abs(w - float(node["width"])),
                abs(h - float(node["height"])),
            )
            match = delta <= TOL_CM
            if not match:
                failures.append("node geometry mismatch:" + sid)
            node_records.append({
                "id": sid,
                "maxGeometryDeltaCm": delta,
                "match": match,
            })

        # Glue evidence for semantic connectors.
        glued = {rid: {"source": False, "target": False} for rid in routes}
        for i in range(1, int(page.Connects.Count) + 1):
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

        semantic_records = []
        semantic_native = 0
        semantic_hidden = 0
        semantic_explicit = 0
        semantic_directional = 0
        semantic_glued = 0

        for rid, route in routes.items():
            conn = by_spec.get(rid)
            if conn is None:
                failures.append("missing semantic connector:" + rid)
                continue

            master_name = ""
            try:
                master_name = str(conn.Master.NameU)
            except Exception:
                pass
            native = master_name == "Association"
            semantic_native += int(native)
            if not native:
                failures.append("semantic connector is not native Association:" + rid)

            hidden = abs(cell_result(conn, "LinePattern", "") - 0.0) <= 1e-9
            semantic_hidden += int(hidden)
            if not hidden:
                failures.append("semantic connector is visible:" + rid)

            bf, ef = formula(conn, "BeginX"), formula(conn, "EndX")
            explicit = "Connections.X" in bf and "Connections.X" in ef
            semantic_explicit += int(explicit)
            if not explicit:
                failures.append("semantic connector not on explicit side ports:" + rid)

            dir_ok = True
            direction_evidence = []
            for endpoint, sid, side in (
                ("source", route["source"], route["sourceSide"]),
                ("target", route["target"], route["targetSide"]),
            ):
                endpoint_formula = bf if endpoint == "source" else ef
                sh = by_spec.get(sid)
                want = {
                    "LEFT": (-1, 0),
                    "RIGHT": (1, 0),
                    "TOP": (0, 1),
                    "BOTTOM": (0, -1),
                }[side]

                evidence = {
                    "endpoint": endpoint,
                    "nodeSpecId": sid,
                    "expectedSide": side,
                    "expectedDir": list(want),
                    "endpointFormula": endpoint_formula,
                }

                if sh is None:
                    evidence["status"] = "FAIL"
                    evidence["error"] = "node shape missing"
                    direction_evidence.append(evidence)
                    dir_ok = False
                    continue

                try:
                    measured = connection_direction_from_endpoint_formula(sh, endpoint_formula)
                    evidence.update(measured)
                    evidence["status"] = (
                        "PASS"
                        if abs(measured["dirX"] - want[0]) <= 1e-6
                        and abs(measured["dirY"] - want[1]) <= 1e-6
                        else "FAIL"
                    )
                except Exception as exc:
                    evidence["status"] = "FAIL"
                    evidence["error"] = repr(exc)

                direction_evidence.append(evidence)
                if evidence["status"] != "PASS":
                    dir_ok = False

            semantic_directional += int(dir_ok)
            if not dir_ok:
                failures.append("semantic port direction mismatch:" + rid)

            glue_ok = glued[rid]["source"] and glued[rid]["target"]
            semantic_glued += int(glue_ok)
            if not glue_ok:
                failures.append("semantic connector unglued:" + rid)

            semantic_records.append({
                "id": rid,
                "master": master_name,
                "nativeAssociation": native,
                "linePattern": formula(conn, "LinePattern"),
                "hidden": hidden,
                "beginFormula": bf,
                "endFormula": ef,
                "explicitSidePorts": explicit,
                "directionalPorts": dir_ok,
                "directionEvidence": direction_evidence,
                "glued": glued[rid],
            })

        # Presentation segment shapes
        overlay_shapes = [
            sh for sh in shapes
            if prop(sh, "Role") == "presentation"
            and prop(sh, "ContentRole") == "route-segment"
        ]
        overlay_by_route = {rid: [] for rid in routes}
        for sh in overlay_shapes:
            owner = prop(sh, "OwnerSpecId")
            if owner in overlay_by_route:
                overlay_by_route[owner].append(sh)
            else:
                failures.append("presentation route with unknown owner:" + str(owner))

        actual_paths = {}
        route_records = []
        total_expected_segments = 0
        total_matching_segments = 0
        exact_route_count = 0
        orthogonal_route_count = 0
        style_segment_count = 0

        for rid, route in routes.items():
            expected_points = route_points(route, nodes_spec)
            expected_segment_count = len(expected_points) - 1
            total_expected_segments += expected_segment_count

            segs = overlay_by_route.get(rid, [])
            indexed = {}
            for sh in segs:
                try:
                    idx = int(float(prop(sh, "SegmentIndex")))
                except Exception:
                    idx = -1
                if idx in indexed:
                    failures.append(f"duplicate presentation segment index:{rid}:{idx}")
                indexed[idx] = sh

            expected_indices = set(range(1, expected_segment_count + 1))
            if set(indexed) != expected_indices:
                failures.append("presentation segment index set:" + rid)

            actual_points = []
            seg_records = []
            all_segments_match = True

            for index in range(1, expected_segment_count + 1):
                sh = indexed.get(index)
                if sh is None:
                    all_segments_match = False
                    continue

                actual_start = logical_endpoint(sh, "Begin", page_h_cm)
                actual_end = logical_endpoint(sh, "End", page_h_cm)
                expected_start = expected_points[index - 1]
                expected_end = expected_points[index]
                delta = max(
                    point_error(actual_start, expected_start),
                    point_error(actual_end, expected_end),
                )
                match = delta <= TOL_CM
                total_matching_segments += int(match)
                all_segments_match &= match

                orth = (
                    abs(actual_start[0] - actual_end[0]) <= TOL_CM
                    or abs(actual_start[1] - actual_end[1]) <= TOL_CM
                )
                if not orth:
                    failures.append(f"non-orthogonal presentation segment:{rid}:{index}")
                    all_segments_match = False

                line_pattern_ok = abs(cell_result(sh, "LinePattern", "") - 1.0) <= 1e-9
                weight_pt = float(sh.CellsU("LineWeight").Result("pt"))
                weight_ok = abs(weight_pt - 0.9) <= 0.1
                colour_ok = colour_formula_ok(formula(sh, "LineColor"), (148, 163, 184))
                style_ok = line_pattern_ok and weight_ok and colour_ok
                style_segment_count += int(style_ok)
                if not style_ok:
                    failures.append(f"presentation segment style:{rid}:{index}")

                if index == 1:
                    actual_points.append(actual_start)
                actual_points.append(actual_end)

                seg_records.append({
                    "index": index,
                    "specId": prop(sh, "SpecId"),
                    "actualStartCm": actual_start,
                    "actualEndCm": actual_end,
                    "expectedStartCm": expected_start,
                    "expectedEndCm": expected_end,
                    "maxEndpointDeltaCm": delta,
                    "match": match,
                    "orthogonal": orth,
                    "styleOk": style_ok,
                    "linePattern": formula(sh, "LinePattern"),
                    "lineColor": formula(sh, "LineColor"),
                    "lineWeightPt": weight_pt,
                })

            actual_paths[rid] = actual_points
            exact_route = (
                len(actual_points) == len(expected_points)
                and all_segments_match
                and max(
                    (point_error(a, b) for a, b in zip(actual_points, expected_points)),
                    default=0.0,
                ) <= TOL_CM
            )
            exact_route_count += int(exact_route)
            orthogonal = path_is_orthogonal(actual_points)
            orthogonal_route_count += int(orthogonal)

            if not exact_route:
                failures.append("presentation route waypoint mismatch:" + rid)
            if not orthogonal:
                failures.append("presentation route not orthogonal:" + rid)

            route_records.append({
                "id": rid,
                "expectedSegmentCount": expected_segment_count,
                "actualSegmentCount": len(segs),
                "expectedPointsCm": expected_points,
                "actualPointsCm": actual_points,
                "exactWaypointMatch": exact_route,
                "orthogonal": orthogonal,
                "segments": seg_records,
            })

        crossing_pairs = count_crossings(actual_paths)
        overlap_pairs = count_overlaps(actual_paths)
        if crossing_pairs:
            failures.append("presentation route crossing")
        if overlap_pairs:
            failures.append("presentation route overlap")

        through = []
        for rid, pts in actual_paths.items():
            route = routes[rid]
            for sid, node in nodes_spec.items():
                if sid in (route["source"], route["target"]):
                    continue
                box = Box(
                    float(node["x"]) - float(node["width"]) / 2,
                    float(node["y"]) - float(node["height"]) / 2,
                    float(node["x"]) + float(node["width"]) / 2,
                    float(node["y"]) + float(node["height"]) / 2,
                )
                for a, b in zip(pts, pts[1:]):
                    if segment_intersects_box_interior(a, b, box):
                        through.append([rid, sid])
                        break
        if through:
            failures.append("presentation route through unrelated node")

        out_of_page = 0
        for rid, pts in actual_paths.items():
            if any(
                p[0] < -TOL_CM
                or p[1] < -TOL_CM
                or p[0] > page_w_cm + TOL_CM
                or p[1] > page_h_cm + TOL_CM
                for p in pts
            ):
                out_of_page += 1
        if out_of_page:
            failures.append("presentation route out of page")

        n_routes = len(routes) or 1
        n_segments = total_expected_segments or 1

        payload = {
            "calibration": "C4F",
            "strategy": "native-semantic-hidden-plus-presentation-segments",
            "status": "PASS" if not failures else "FAIL",
            "semanticConnectorCount": len(routes),
            "nativeAssociationRatio": semantic_native / n_routes,
            "semanticFullyGluedRatio": semantic_glued / n_routes,
            "semanticExplicitSidePortRatio": semantic_explicit / n_routes,
            "semanticDirectionalSidePortRatio": semantic_directional / n_routes,
            "semanticHiddenStrokeRatio": semantic_hidden / n_routes,
            "presentationExpectedSegmentCount": total_expected_segments,
            "presentationActualSegmentCount": len(overlay_shapes),
            "presentationSegmentGeometryMatchRatio": total_matching_segments / n_segments,
            "presentationSegmentStyleRatio": style_segment_count / n_segments,
            "presentationExactRouteRatio": exact_route_count / n_routes,
            "presentationOrthogonalRouteRatio": orthogonal_route_count / n_routes,
            "connectorConnectorCrossingCount": len(crossing_pairs),
            "connectorOverlapPairCount": len(overlap_pairs),
            "connectorThroughUnrelatedNodeCount": len(through),
            "outOfPageCount": out_of_page,
            "forbiddenTokenCounts": error_tokens,
            "nodes": node_records,
            "semanticConnectors": semantic_records,
            "routes": route_records,
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
