"""Build the C3 presentation-layer calibration from a fresh Visio document."""
from __future__ import annotations

import json
import os
import subprocess
import sys

import win32com.client
import yaml

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from presentation import (  # noqa: E402
    cm_to_in,
    set_geometry_from_center,
    style_presentation_box,
    style_text,
)
from render_core import resolve_font_id, set_prop  # noqa: E402

HERE = os.path.dirname(__file__)
RENDERER = os.path.abspath(os.path.join(HERE, ".."))
ROOT = os.path.abspath(os.path.join(RENDERER, ".."))
OUT = os.path.join(HERE, "out")
SPEC = os.path.join(HERE, "c3-presentation-spec.yaml")
SUMMARY = os.path.join(OUT, "calibration-summary.json")


def _write_summary(c3: str) -> None:
    payload = {"C1": "FROZEN_PASS", "C2": "FROZEN_PASS", "C3": c3, "C4": "BLOCKED"}
    with open(SUMMARY, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)


def main() -> int:
    os.makedirs(OUT, exist_ok=True)

    # Static tests are part of the same build and cannot be stale.
    tr = subprocess.run(
        [sys.executable, "-m", "pytest", os.path.join(RENDERER, "tests"), "-q"],
        cwd=RENDERER,
        capture_output=True,
        text=True,
    )
    with open(os.path.join(OUT, "static-test-report.json"), "w", encoding="utf-8") as f:
        json.dump(
            {
                "status": "PASS" if tr.returncode == 0 else "FAIL",
                "stdout": tr.stdout,
                "stderr": tr.stderr,
            },
            f,
            ensure_ascii=False,
            indent=2,
        )
    if tr.returncode != 0:
        _write_summary("FAIL")
        return tr.returncode

    spec = yaml.safe_load(open(SPEC, encoding="utf-8"))
    page_spec = spec["page"]
    page_w_cm = float(page_spec["widthCm"])
    page_h_cm = float(page_spec["heightCm"])

    # Use an isolated automation instance so a resident MCP Visio process
    # cannot change the COM class/page object returned to this calibration.
    app = win32com.client.DispatchEx("Visio.Application")
    app.Visible = False
    app.AlertResponse = 7
    doc = app.Documents.Add("")
    page = doc.Pages.Item(1)
    page.NameU = "C3_Presentation"
    page.PageSheet.CellsU("PageWidth").FormulaU = f"{cm_to_in(page_w_cm)} in"
    page.PageSheet.CellsU("PageHeight").FormulaU = f"{cm_to_in(page_h_cm)} in"
    font_id = resolve_font_id(doc, spec["font"]["family"])

    created = []
    temp_vsdx = None
    try:
        for item in spec["presentation"]:
            # Create a generic editable presentation shape, then apply final geometry.
            sh = page.DrawRectangle(0, 0, 0.1, 0.1)
            set_prop(sh, "SpecId", item["id"])
            set_prop(sh, "Role", "presentation")
            set_prop(sh, "ContentRole", item["role"])
            set_geometry_from_center(
                sh,
                x_cm=float(item["x"]),
                y_cm=float(item["y"]),
                w_cm=float(item["width"]),
                h_cm=float(item["height"]),
                page_h_cm=page_h_cm,
            )
            style_presentation_box(
                sh,
                fill=item.get("fill"),
                stroke=item.get("stroke"),
                line_weight_pt=float(item.get("lineWeightPt", 0.8)),
            )
            if item.get("text"):
                sh.Text = str(item["text"])
                style_text(
                    sh,
                    font_id=font_id,
                    color=item.get("textColor", "#0F172A"),
                    size_pt=float(item.get("fontSizePt", 9)),
                    horizontal=item.get("horizontal", "left"),
                    vertical=item.get("vertical", "middle"),
                )
            else:
                sh.Text = ""
            if item["id"] == "BG-CANVAS":
                try:
                    sh.SendToBack()
                except Exception:
                    pass
            created.append({"SpecId": item["id"], "shapeId": int(sh.ID)})

        vsdx = os.path.join(OUT, "C3_Presentation.vsdx")
        svg = os.path.join(OUT, "C3_Presentation.raw.svg")
        png = os.path.join(OUT, "C3_Presentation.png")
        # Save to a fresh sibling first; Visio refuses SaveAs over an existing
        # read-only/previously opened artifact.  Replace only after Visio has
        # closed the document, leaving a deterministic C3_Presentation.vsdx.
        temp_vsdx = vsdx + ".new"
        doc.SaveAs(temp_vsdx)
        page.Export(svg)
        page.Export(png)
    finally:
        try:
            doc.Close()
        except Exception:
            pass
        app.Quit()
    if temp_vsdx and os.path.exists(temp_vsdx):
        os.replace(temp_vsdx, vsdx)

    validator = os.path.join(HERE, "validate_c3.py")
    rc = subprocess.run([sys.executable, validator], cwd=ROOT).returncode
    _write_summary("FROZEN_PASS" if rc == 0 else "FAIL")
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
