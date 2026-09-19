"""Cross-platform OpenXML audit for C4 fallback semantic port directions.

This does not replace the COM validator. It exists to independently prove that
the persisted VSDX contains the expected DirX/DirY values on the exact
connection-point rows referenced by each hidden native Association.
"""
from __future__ import annotations

import json
import re
import sys
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

import yaml

NS = {"v": "http://schemas.microsoft.com/office/visio/2012/main"}


def prop(shape, name: str):
    for section in shape.findall("v:Section", NS):
        if section.get("N") != "Property":
            continue
        for row in section.findall("v:Row", NS):
            if row.get("N") != name:
                continue
            for cell in row.findall("v:Cell", NS):
                if cell.get("N") == "Value":
                    return cell.get("V")
    return None


def top_cell(shape, name: str):
    for cell in shape.findall("v:Cell", NS):
        if cell.get("N") == name:
            return {"V": cell.get("V"), "F": cell.get("F")}
    return None


def connection_row(shape, row_index: int):
    for section in shape.findall("v:Section", NS):
        if section.get("N") != "Connection":
            continue
        for row in section.findall("v:Row", NS):
            if int(row.get("IX")) != row_index:
                continue
            data = {"IX": row_index}
            for cell in row.findall("v:Cell", NS):
                data[cell.get("N")] = cell.get("V")
            return data
    return None


def expected_dir(side: str):
    return {
        "LEFT": (-1.0, 0.0),
        "RIGHT": (1.0, 0.0),
        "TOP": (0.0, 1.0),
        "BOTTOM": (0.0, -1.0),
    }[side]


def main() -> int:
    renderer = Path(__file__).resolve().parents[1]
    spec_path = Path(__file__).with_name("c4-routing-calibration-spec.yaml")
    vsdx_path = Path(__file__).with_name("out") / "C4F_SemanticOverlay.vsdx"
    report_path = Path(__file__).with_name("out") / "C4F-OpenXML-Direction-Audit.json"

    spec = yaml.safe_load(spec_path.read_text(encoding="utf-8"))
    routes = {r["id"]: r for r in spec["routes"]}

    with zipfile.ZipFile(vsdx_path) as zf:
        page_xml = ET.fromstring(zf.read("visio/pages/page1.xml"))

    shapes = page_xml.find("v:Shapes", NS)
    if shapes is None:
        raise RuntimeError("page contains no Shapes collection")

    by_spec = {}
    for shape in list(shapes):
        sid = prop(shape, "SpecId")
        if sid:
            by_spec[sid] = shape

    failures = []
    records = []

    for rid, route in routes.items():
        conn = by_spec.get(rid)
        if conn is None:
            failures.append(f"missing semantic connector:{rid}")
            continue

        line_pattern = top_cell(conn, "LinePattern")
        hidden = line_pattern is not None and str(line_pattern.get("V")) == "0"
        if not hidden:
            failures.append(f"semantic connector stroke not hidden:{rid}")

        route_record = {
            "id": rid,
            "nameU": conn.get("NameU"),
            "hiddenStroke": hidden,
            "endpoints": [],
        }

        for endpoint, node_id, side, cell_name in (
            ("source", route["source"], route["sourceSide"], "BeginX"),
            ("target", route["target"], route["targetSide"], "EndX"),
        ):
            node = by_spec.get(node_id)
            cell = top_cell(conn, cell_name)
            formula = "" if cell is None else (cell.get("F") or "")
            match = re.search(r"Connections\.X(\d+)", formula)

            rec = {
                "endpoint": endpoint,
                "nodeSpecId": node_id,
                "expectedSide": side,
                "formula": formula,
            }

            if node is None or match is None:
                rec["status"] = "FAIL"
                rec["error"] = "missing node or explicit Connections.XN formula"
                failures.append(f"direction evidence unavailable:{rid}:{endpoint}")
                route_record["endpoints"].append(rec)
                continue

            alias_index = int(match.group(1))
            row_index = alias_index - 1
            row = connection_row(node, row_index)
            rec["aliasIndex"] = alias_index
            rec["rowIndex"] = row_index

            if row is None:
                rec["status"] = "FAIL"
                rec["error"] = "referenced connection row not found"
                failures.append(f"connection row missing:{rid}:{endpoint}")
                route_record["endpoints"].append(rec)
                continue

            dx = float(row.get("DirX", "nan"))
            dy = float(row.get("DirY", "nan"))
            want = expected_dir(side)
            ok = abs(dx - want[0]) <= 1e-9 and abs(dy - want[1]) <= 1e-9

            rec.update({
                "dirX": dx,
                "dirY": dy,
                "expectedDir": list(want),
                "status": "PASS" if ok else "FAIL",
            })
            if not ok:
                failures.append(f"direction mismatch:{rid}:{endpoint}")

            route_record["endpoints"].append(rec)

        records.append(route_record)

    payload = {
        "audit": "C4F OpenXML directional ports",
        "status": "PASS" if not failures else "FAIL",
        "routeCount": len(routes),
        "routes": records,
        "failures": failures,
    }

    report_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=True, indent=2))
    return 0 if payload["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
