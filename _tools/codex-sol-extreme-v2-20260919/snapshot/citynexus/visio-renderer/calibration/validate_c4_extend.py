"""Independent validator for C4 Extend fallback calibration."""
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
SPEC_PATH = os.path.join(HERE, "c4-extend-calibration-spec.yaml")
VSDX = os.path.join(OUT, "C4E_ExtendFallback.vsdx")
SVG = os.path.join(OUT, "C4E_ExtendFallback.raw.svg")
REPORT = os.path.join(OUT, "C4E_ExtendFallback-report.json")

TOL_CM = 0.05
VIS_SECTION_CONNECTION = 7
VIS_CNNCT_DIRX = 2
VIS_CNNCT_DIRY = 3


def prop(shape, name: str) -> str | None:
    try:
        if not int(shape.CellExistsU("Prop." + name, 0)):
            return None
        return str(shape.CellsU("Prop." + name).ResultStr("")).strip()
    except Exception:
        return None


def formula(shape, name: str) -> str:
    try:
        return str(shape.CellsU(name).FormulaU)
    except Exception:
        return ""


def result(shape, name: str, units: str = "") -> float:
    return float(shape.CellsU(name).Result(units))


def point_error(a, b) -> float:
    return math.hypot(float(a[0]) - float(b[0]), float(a[1]) - float(b[1]))


def logical_endpoint(shape, which: str, page_h_cm: float) -> tuple[float, float]:
    return (
        result(shape, which + "X", "inches") * 2.54,
        page_h_cm - result(shape, which + "Y", "inches") * 2.54,
    )


def logical_center(shape, page_h_cm: float) -> tuple[float, float]:
    return (
        result(shape, "PinX", "inches") * 2.54,
        page_h_cm - result(shape, "PinY", "inches") * 2.54,
    )


def connection_direction(shape, endpoint_formula: str) -> dict:
    match = re.search(r"Connections\.X(\d+)", endpoint_formula)
    if match is None:
        raise ValueError(f"not glued to Connections.XN: {endpoint_formula}")
    alias_index = int(match.group(1))
    row_index = alias_index - 1
    dx = float(shape.CellsSRC(VIS_SECTION_CONNECTION, row_index, VIS_CNNCT_DIRX).Result(""))
    dy = float(shape.CellsSRC(VIS_SECTION_CONNECTION, row_index, VIS_CNNCT_DIRY).Result(""))
    return {
        "aliasIndex": alias_index,
        "rowIndex": row_index,
        "dirX": dx,
        "dirY": dy,
    }


def font_name(doc, shape) -> str:
    try:
        font_id = int(round(result(shape, "Char.Font")))
        return str(doc.Fonts.Item(font_id).Name)
    except Exception:
        return ""


def expected_dir(side: str):
    return {
        "LEFT": (-1.0, 0.0),
        "RIGHT": (1.0, 0.0),
        "TOP": (0.0, 1.0),
        "BOTTOM": (0.0, -1.0),
    }[side]


def colour_ok(formula_u: str, rgb: tuple[int, int, int]) -> bool:
    compact = re.sub(r"\s+", "", str(formula_u)).upper()
    return compact == f"RGB({rgb[0]},{rgb[1]},{rgb[2]})"


def main() -> int:
    with open(SPEC_PATH, encoding="utf-8") as handle:
        spec = yaml.safe_load(handle)

    page_h = float(spec["page"]["heightCm"])
    page_w = float(spec["page"]["widthCm"])
    nodes_spec = {n["id"]: n for n in spec["nodes"]}
    routes = {r["id"]: r for r in spec["routes"]}
    failures = []

    if not os.path.exists(VSDX) or not os.path.exists(SVG):
        payload = {"calibration": "C4E", "status": "FAIL", "failures": ["missing C4E artifacts"]}
        with open(REPORT, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2)
        return 1

    svg_text = open(SVG, encoding="utf-8", errors="ignore").read()
    with zipfile.ZipFile(VSDX) as zf:
        xml = "\n".join(
            zf.read(name).decode("utf-8", "ignore")
            for name in zf.namelist()
            if name.endswith(".xml")
        )
    error_tokens = {t: xml.count(t) + svg_text.count(t) for t in ("#VALUE!", "#REF!", "#NAME?")}
    if any(error_tokens.values()):
        failures.append("ShapeSheet error token")

    app = win32com.client.DispatchEx("Visio.Application")
    app.Visible = False
    app.AlertResponse = 7
    doc = app.Documents.Open(VSDX)

    try:
        page = doc.Pages.Item(1)
        shapes = []
        by_spec = {}
        for i in range(1, int(page.Shapes.Count) + 1):
            shape = page.Shapes.Item(i)
            shapes.append(shape)
            sid = prop(shape, "SpecId")
            if sid:
                if sid in by_spec:
                    failures.append("duplicate SpecId:" + sid)
                by_spec[sid] = shape

        # Semantic glue map.
        glued = {rid: {"source": False, "target": False} for rid in routes}
        for i in range(1, int(page.Connects.Count) + 1):
            try:
                c = page.Connects.Item(i)
                fs, ts = c.FromSheet, c.ToSheet
                fsid, tsid = prop(fs, "SpecId"), prop(ts, "SpecId")
                if fsid in routes and tsid in nodes_spec:
                    glued[fsid]["source"] |= tsid == routes[fsid]["source"]
                    glued[fsid]["target"] |= tsid == routes[fsid]["target"]
                elif tsid in routes and fsid in nodes_spec:
                    glued[tsid]["source"] |= fsid == routes[tsid]["source"]
                    glued[tsid]["target"] |= fsid == routes[tsid]["target"]
            except Exception:
                pass

        native_count = hidden_count = glued_count = explicit_count = directional_count = 0
        semantic_records = []

        for rid, route in routes.items():
            conn = by_spec.get(rid)
            if conn is None:
                failures.append("missing native Extend:" + rid)
                continue

            try:
                master_name = str(conn.Master.NameU)
            except Exception:
                master_name = ""

            native = master_name == "Extend"
            native_count += int(native)
            if not native:
                failures.append("semantic connector is not native Extend:" + rid)

            connector_type_ok = prop(conn, "ConnectorType") == "extend"
            if not connector_type_ok:
                failures.append("ConnectorType mismatch:" + rid)

            hidden = abs(result(conn, "LinePattern") - 0.0) <= 1e-9
            hidden_count += int(hidden)
            if not hidden:
                failures.append("native Extend stroke visible:" + rid)

            bf, ef = formula(conn, "BeginX"), formula(conn, "EndX")
            explicit = "Connections.X" in bf and "Connections.X" in ef
            explicit_count += int(explicit)
            if not explicit:
                failures.append("native Extend not on explicit side ports:" + rid)

            direction_evidence = []
            dir_ok = True
            for endpoint, node_id, side, endpoint_formula in (
                ("source", route["source"], route["sourceSide"], bf),
                ("target", route["target"], route["targetSide"], ef),
            ):
                evidence = {
                    "endpoint": endpoint,
                    "nodeSpecId": node_id,
                    "expectedSide": side,
                    "expectedDir": list(expected_dir(side)),
                    "endpointFormula": endpoint_formula,
                }
                try:
                    measured = connection_direction(by_spec[node_id], endpoint_formula)
                    evidence.update(measured)
                    want = expected_dir(side)
                    ok = abs(measured["dirX"] - want[0]) <= 1e-6 and abs(measured["dirY"] - want[1]) <= 1e-6
                    evidence["status"] = "PASS" if ok else "FAIL"
                except Exception as exc:
                    evidence["status"] = "FAIL"
                    evidence["error"] = repr(exc)
                    ok = False
                direction_evidence.append(evidence)
                dir_ok &= ok
            directional_count += int(dir_ok)
            if not dir_ok:
                failures.append("directional port mismatch:" + rid)

            glue_ok = glued[rid]["source"] and glued[rid]["target"]
            glued_count += int(glue_ok)
            if not glue_ok:
                failures.append("native Extend unglued:" + rid)

            arrow_code = int(float(prop(conn, "NativeArrowCode") or "0"))
            if arrow_code <= 0:
                failures.append("missing native Extend arrow evidence:" + rid)

            semantic_records.append({
                "id": rid,
                "master": master_name,
                "nativeExtend": native,
                "connectorType": prop(conn, "ConnectorType"),
                "hiddenStroke": hidden,
                "beginFormula": bf,
                "endFormula": ef,
                "explicitSidePorts": explicit,
                "directionalPorts": dir_ok,
                "directionEvidence": direction_evidence,
                "glued": glued[rid],
                "nativeArrowCode": arrow_code,
                "nativeArrowSourceCell": prop(conn, "NativeArrowSourceCell"),
            })

        # Presentation route segments.
        paths = {}
        route_records = []
        expected_segment_total = actual_segment_total = 0
        geometry_match_count = style_match_count = terminal_arrow_count = 0
        exact_route_count = orthogonal_route_count = 0

        for rid, route in routes.items():
            expected_points = route_points(route, nodes_spec)
            expected_segment_count = len(expected_points) - 1
            expected_segment_total += expected_segment_count

            segs = [
                shape for shape in shapes
                if prop(shape, "Role") == "presentation"
                and prop(shape, "ContentRole") == "extend-route-segment"
                and prop(shape, "OwnerSpecId") == rid
            ]
            actual_segment_total += len(segs)

            indexed = {}
            for shape in segs:
                try:
                    idx = int(float(prop(shape, "SegmentIndex") or "-1"))
                except Exception:
                    idx = -1
                indexed[idx] = shape

            if set(indexed) != set(range(1, expected_segment_count + 1)):
                failures.append("presentation segment index set:" + rid)

            actual_points = []
            segment_records = []
            route_ok = True
            arrow_code = int(float(prop(by_spec[rid], "NativeArrowCode") or "0"))

            for index in range(1, expected_segment_count + 1):
                shape = indexed.get(index)
                if shape is None:
                    route_ok = False
                    continue

                start = logical_endpoint(shape, "Begin", page_h)
                end = logical_endpoint(shape, "End", page_h)
                exp_start, exp_end = expected_points[index - 1], expected_points[index]
                delta = max(point_error(start, exp_start), point_error(end, exp_end))
                geom_ok = delta <= TOL_CM
                geometry_match_count += int(geom_ok)
                route_ok &= geom_ok

                orth = abs(start[0] - end[0]) <= TOL_CM or abs(start[1] - end[1]) <= TOL_CM
                route_ok &= orth

                pattern_ok = abs(result(shape, "LinePattern") - 2.0) <= 1e-9
                weight_ok = abs(result(shape, "LineWeight", "pt") - 0.85) <= 0.1
                line_colour_ok = colour_ok(formula(shape, "LineColor"), (148, 163, 184))
                style_ok = pattern_ok and weight_ok and line_colour_ok
                style_match_count += int(style_ok)
                if not style_ok:
                    failures.append(f"extend presentation style:{rid}:{index}")

                begin_arrow = int(round(result(shape, "BeginArrow")))
                end_arrow = int(round(result(shape, "EndArrow")))
                terminal = index == expected_segment_count
                arrow_ok = begin_arrow == 0 and end_arrow == (arrow_code if terminal else 0)
                if terminal and arrow_ok:
                    terminal_arrow_count += 1
                if not arrow_ok:
                    failures.append(f"extend arrow placement:{rid}:{index}")

                if index == 1:
                    actual_points.append(start)
                actual_points.append(end)

                segment_records.append({
                    "index": index,
                    "specId": prop(shape, "SpecId"),
                    "actualStartCm": start,
                    "actualEndCm": end,
                    "expectedStartCm": exp_start,
                    "expectedEndCm": exp_end,
                    "maxEndpointDeltaCm": delta,
                    "geometryMatch": geom_ok,
                    "orthogonal": orth,
                    "styleMatch": style_ok,
                    "beginArrow": begin_arrow,
                    "endArrow": end_arrow,
                    "arrowMatch": arrow_ok,
                })

            paths[rid] = actual_points
            exact = (
                len(actual_points) == len(expected_points)
                and route_ok
                and max((point_error(a, b) for a, b in zip(actual_points, expected_points)), default=0.0) <= TOL_CM
            )
            exact_route_count += int(exact)
            orthogonal = path_is_orthogonal(actual_points)
            orthogonal_route_count += int(orthogonal)
            if not exact:
                failures.append("extend route waypoint mismatch:" + rid)
            if not orthogonal:
                failures.append("extend route not orthogonal:" + rid)

            route_records.append({
                "id": rid,
                "expectedPointsCm": expected_points,
                "actualPointsCm": actual_points,
                "exactWaypointMatch": exact,
                "orthogonal": orthogonal,
                "segments": segment_records,
            })

        # Label / condition shapes.
        label_records = []
        label_count = condition_count = label_style_count = 0
        for rid, route in routes.items():
            for suffix, content_role, expected_text, box_key in (
                ("LABEL", "extend-label", route["label"], "labelBox"),
                ("CONDITION", "extend-condition", route["condition"], "conditionBox"),
            ):
                sid = f"{rid}::{suffix}"
                shape = by_spec.get(sid)
                if shape is None:
                    failures.append("missing extend text shape:" + sid)
                    continue

                role_ok = prop(shape, "Role") == "presentation" and prop(shape, "ContentRole") == content_role
                owner_ok = prop(shape, "OwnerSpecId") == rid
                text_ok = str(shape.Text).strip() == expected_text
                center = logical_center(shape, page_h)
                expected_center = (float(route[box_key]["x"]), float(route[box_key]["y"]))
                geometry_ok = point_error(center, expected_center) <= TOL_CM
                no_box = abs(result(shape, "FillPattern")) <= 1e-9 and abs(result(shape, "LinePattern")) <= 1e-9
                font = font_name(doc, shape)
                font_ok = font.lower() in {"segoe ui", "aptos"}
                style_ok = no_box and font_ok

                if suffix == "LABEL":
                    label_count += int(text_ok and role_ok and owner_ok and geometry_ok)
                else:
                    condition_count += int(text_ok and role_ok and owner_ok and geometry_ok)
                label_style_count += int(style_ok)

                if not (text_ok and role_ok and owner_ok and geometry_ok and style_ok):
                    failures.append("extend text validation:" + sid)

                label_records.append({
                    "specId": sid,
                    "ownerSpecId": prop(shape, "OwnerSpecId"),
                    "contentRole": prop(shape, "ContentRole"),
                    "text": str(shape.Text).strip(),
                    "expectedText": expected_text,
                    "centerCm": center,
                    "expectedCenterCm": expected_center,
                    "geometryMatch": geometry_ok,
                    "font": font,
                    "styleMatch": style_ok,
                })

        crossing_pairs = count_crossings(paths)
        overlap_pairs = count_overlaps(paths)
        if crossing_pairs:
            failures.append("extend route crossing")
        if overlap_pairs:
            failures.append("extend route overlap")

        through = []
        for rid, points in paths.items():
            route = routes[rid]
            for node_id, node in nodes_spec.items():
                if node_id in (route["source"], route["target"]):
                    continue
                box = Box(
                    float(node["x"]) - float(node["width"]) / 2,
                    float(node["y"]) - float(node["height"]) / 2,
                    float(node["x"]) + float(node["width"]) / 2,
                    float(node["y"]) + float(node["height"]) / 2,
                )
                for a, b in zip(points, points[1:]):
                    if segment_intersects_box_interior(a, b, box):
                        through.append([rid, node_id])
                        break
        if through:
            failures.append("extend route through unrelated node")

        out_of_page = 0
        for points in paths.values():
            if any(
                x < -TOL_CM or y < -TOL_CM or x > page_w + TOL_CM or y > page_h + TOL_CM
                for x, y in points
            ):
                out_of_page += 1
        if out_of_page:
            failures.append("extend route out of page")

        # Presentation SVG should contain exactly the intended relationship labels.
        visible_extend_count = svg_text.count("&lt;&lt;extend&gt;&gt;") + svg_text.count("<<extend>>")
        for route in routes.values():
            if route["condition"] not in svg_text:
                failures.append("condition missing from raw SVG:" + route["id"])
        if visible_extend_count < len(routes):
            failures.append("extend label missing from raw SVG")

        n_routes = len(routes) or 1
        n_segments = expected_segment_total or 1
        n_text = len(routes) * 2 or 1

        payload = {
            "calibration": "C4E",
            "strategy": "native-extend-hidden-plus-presentation-segments",
            "status": "PASS" if not failures else "FAIL",
            "semanticExtendCount": len(routes),
            "nativeExtendRatio": native_count / n_routes,
            "semanticFullyGluedRatio": glued_count / n_routes,
            "semanticExplicitSidePortRatio": explicit_count / n_routes,
            "semanticDirectionalSidePortRatio": directional_count / n_routes,
            "semanticHiddenStrokeRatio": hidden_count / n_routes,
            "presentationExpectedSegmentCount": expected_segment_total,
            "presentationActualSegmentCount": actual_segment_total,
            "presentationSegmentGeometryMatchRatio": geometry_match_count / n_segments,
            "presentationSegmentStyleRatio": style_match_count / n_segments,
            "presentationExactRouteRatio": exact_route_count / n_routes,
            "presentationOrthogonalRouteRatio": orthogonal_route_count / n_routes,
            "terminalOpenArrowRatio": terminal_arrow_count / n_routes,
            "extendLabelRatio": label_count / n_routes,
            "extendConditionRatio": condition_count / n_routes,
            "extendTextStyleRatio": label_style_count / n_text,
            "connectorConnectorCrossingCount": len(crossing_pairs),
            "connectorOverlapPairCount": len(overlap_pairs),
            "connectorThroughUnrelatedNodeCount": len(through),
            "outOfPageCount": out_of_page,
            "forbiddenTokenCounts": error_tokens,
            "semanticConnectors": semantic_records,
            "routes": route_records,
            "textShapes": label_records,
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
