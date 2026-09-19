from pathlib import Path
import copy
import sys

import yaml

HERE = Path(__file__).resolve().parent
CAL = HERE.parent / 'calibration'
sys.path[:0] = [str(CAL), str(HERE.parent)]

from route_p1_negotiated_grid import load
from search_p1_global_port_rotations import genus
from search_p1_local_bundle_ports import _strategic_variants, _skeleton_candidate


def test_strategic_local_variants_are_genus_zero_and_keep_unique_uc06_ports():
    sem, original, nodes, routes, overrides, frozen, mutable = load('PLAN_TRAVELER_SKELETON_PLANAR_GRID')
    variants = _strategic_variants(routes, nodes, 12)
    assert variants
    for _, candidate_routes in variants:
        assert genus(candidate_routes, nodes) == 0
        a = candidate_routes['A-T-UC-06']
        b = candidate_routes['A-B-06']
        assert not (
            a['targetSide'] == b['targetSide']
            and abs(float(a['targetPortFraction']) - float(b['targetPortFraction'])) < 1e-9
        )


def test_skeleton_candidate_requires_identical_endpoint_ports(tmp_path):
    sem, original, nodes, routes, overrides, frozen, mutable = load('PLAN_TRAVELER_SKELETON_PLANAR_GRID')
    # Build a minimal exact skeleton from the current route itself.
    route = copy.deepcopy(routes['A-T-UC-07'])
    route['waypoints'] = [[5.6, 9.5], [5.6, 9.9], [14.4, 9.9], [14.4, 8.2]]
    skeleton = {route['id']: route}
    assert _skeleton_candidate(routes['A-T-UC-07'], nodes, skeleton) is not None

    changed = copy.deepcopy(routes['A-T-UC-07'])
    changed['targetPortFraction'] = 0.6
    assert _skeleton_candidate(changed, nodes, skeleton) is None
