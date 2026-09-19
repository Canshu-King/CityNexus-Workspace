from pathlib import Path
import ast
import yaml

ROOT = Path(__file__).resolve().parents[1]


def route_points(route: dict, nodes: dict[str, dict]):
    def side_port(node, side, fraction=0.5):
        left = float(node["x"]) - float(node["width"]) / 2
        right = float(node["x"]) + float(node["width"]) / 2
        top = float(node["y"]) - float(node["height"]) / 2
        bottom = float(node["y"]) + float(node["height"]) / 2
        f = float(fraction)
        if side == "LEFT":
            return (left, top + (bottom - top) * f)
        if side == "RIGHT":
            return (right, top + (bottom - top) * f)
        if side == "TOP":
            return (left + (right - left) * f, top)
        if side == "BOTTOM":
            return (left + (right - left) * f, bottom)
        raise ValueError(side)

    start = side_port(
        nodes[route["source"]],
        route["sourceSide"],
        route.get("sourcePortFraction", 0.5),
    )
    end = side_port(
        nodes[route["target"]],
        route["targetSide"],
        route.get("targetPortFraction", 0.5),
    )
    return [start, *[tuple(map(float, p)) for p in route.get("waypoints", [])], end]


def segment_dir(a, b):
    dx = b[0] - a[0]
    dy = b[1] - a[1]
    if abs(dx) > 1e-9 and abs(dy) > 1e-9:
        return None
    if abs(dx) > 1e-9:
        return (1 if dx > 0 else -1, 0)
    if abs(dy) > 1e-9:
        return (0, 1 if dy > 0 else -1)
    return (0, 0)


def outward(side):
    return {
        "LEFT": (-1, 0),
        "RIGHT": (1, 0),
        "TOP": (0, -1),
        "BOTTOM": (0, 1),
    }[side]


def test_c4e1_spec_routes_leave_and_enter_the_declared_sides_normally():
    spec = yaml.safe_load(
        (ROOT / "calibration" / "c4-extend-calibration-spec-v0.1.1.yaml")
        .read_text(encoding="utf-8")
    )
    nodes = {n["id"]: n for n in spec["nodes"]}

    assert [r["id"] for r in spec["routes"]] == [
        "EXT-07-06",
        "EXT-09-08",
        "EXT-10-09",
    ]

    for route in spec["routes"]:
        points = route_points(route, nodes)
        source_actual = segment_dir(points[0], points[1])
        target_actual = segment_dir(points[-2], points[-1])

        source_expected = outward(route["sourceSide"])
        target_out = outward(route["targetSide"])
        target_expected = (-target_out[0], -target_out[1])

        assert source_actual == source_expected, route["id"]
        assert target_actual == target_expected, route["id"]


def test_c4e1_ext_07_06_approaches_bottom_port_vertically():
    spec = yaml.safe_load(
        (ROOT / "calibration" / "c4-extend-calibration-spec-v0.1.1.yaml")
        .read_text(encoding="utf-8")
    )
    nodes = {n["id"]: n for n in spec["nodes"]}
    route = next(r for r in spec["routes"] if r["id"] == "EXT-07-06")
    points = route_points(route, nodes)

    assert points[-2] == (11.1, 9.7)
    assert points[-1][0] == 11.1
    assert points[-2][1] > points[-1][1]


def test_c4e1_validator_parses_svg_text_and_checks_endpoint_tangents():
    src = (
        ROOT / "calibration" / "validate_c4_extend_1.py"
    ).read_text(encoding="utf-8")

    assert "ET.parse(svg_path)" in src
    assert "visible_svg_texts" in src
    assert "presentationEndpointTangentRatio" in src
    assert "endpointTangentEvidence" in src
    assert 'svg_text.count("&lt;&lt;extend&gt;&gt;")' not in src


def test_c4e1_builder_keeps_native_extend_and_no_geometry_mutation():
    src = (
        ROOT / "calibration" / "build_c4_extend_1.py"
    ).read_text(encoding="utf-8")
    tree = ast.parse(src)

    assert 'Masters.ItemU("Extend")' in src
    assert 'conn.CellsU("BeginX").GlueTo' in src
    assert 'conn.CellsU("EndX").GlueTo' in src
    assert "VIS_SECTION_GEOMETRY_1" not in src

    delete_calls = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "DeleteRow"
    ]
    assert delete_calls == []
