from pathlib import Path
import sys
import yaml

RENDERER = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RENDERER))
from routing_geometry import count_crossings, count_overlaps, node_box, path_is_orthogonal, route_points, segment_intersects_box_interior


def test_c4_calibration_plan_is_clean():
    spec = yaml.safe_load((RENDERER / 'calibration' / 'c4-routing-calibration-spec.yaml').read_text(encoding='utf8'))
    nodes = {x['id']: x for x in spec['nodes']}
    paths = {}
    for route in spec['routes']:
        pts = route_points(route, nodes)
        assert path_is_orthogonal(pts), route['id']
        for nid, node in nodes.items():
            if nid in {route['source'], route['target']}:
                continue
            assert not any(segment_intersects_box_interior(a, b, node_box(node)) for a, b in zip(pts, pts[1:])), (route['id'], nid)
        paths[route['id']] = pts
    assert count_crossings(paths) == []
    assert count_overlaps(paths) == []
