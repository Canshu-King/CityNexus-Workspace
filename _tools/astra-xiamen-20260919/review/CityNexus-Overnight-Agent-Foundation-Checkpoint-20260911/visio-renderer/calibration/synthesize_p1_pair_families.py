"""Targeted pairwise homotopy synthesis for P1 Association candidate pools.

Use this only after ``diagnose_p1_candidate_pool.py`` reports a route pair with
zero compatible candidate pairs.  It treats one candidate as an exact hard
obstacle and reroutes the other route, then swaps direction.  Any returned pair
is proof that the *port plan* can separate those two routes and that the
candidate generator simply lacked the necessary homotopy family.

This is a diagnostic/family generator.  It never edits the authoritative
candidate and never claims that a pairwise solution extends to all 18 routes.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent), str(HERE)]

from explore_p1_disjoint_pool import _candidate_pool
from route_candidate_selector import candidates_contact
from route_p1_negotiated_grid import build_axes, build_graph, load, topology_gate


def _points(candidate):
    return [(x / 200.0, y / 200.0) for x, y in candidate.points]


def _base_pool(route, nodes, xs, ys, frozen, samples, seed):
    ix, iy, allowed = build_graph(xs, ys, nodes, frozen)
    return _candidate_pool(route, nodes, xs, ys, ix, iy, allowed, samples, seed)


def run(*, plan, route_a, route_b, base_samples, synth_samples, fixed_limit, seed, output):
    sem, _, nodes, routes, _, frozen, mutable = load(plan)
    by_id = {route["id"]: route for route in mutable}
    if route_a not in by_id or route_b not in by_id:
        raise SystemExit(f"routes must be mutable Associations: {route_a}, {route_b}")
    xs, ys = build_axes(sem, mutable, nodes, frozen)

    pool_a = _base_pool(by_id[route_a], nodes, xs, ys, frozen, base_samples, seed + 101)
    pool_b = _base_pool(by_id[route_b], nodes, xs, ys, frozen, base_samples, seed + 202)
    direct_pairs = [
        (a, b) for a in pool_a for b in pool_b if not candidates_contact(a, b)
    ]

    synthesized = []
    directions = (
        (route_a, pool_a, route_b, by_id[route_b], seed + 3001),
        (route_b, pool_b, route_a, by_id[route_a], seed + 6001),
    )
    for fixed_rid, fixed_pool, reroute_rid, reroute, direction_seed in directions:
        for index, fixed in enumerate(sorted(fixed_pool, key=lambda c: (c.cost, c.key))[:fixed_limit]):
            hard = dict(frozen)
            hard[f"__pair_fixed__:{fixed_rid}"] = _points(fixed)
            ix, iy, allowed = build_graph(xs, ys, nodes, hard)
            generated = _candidate_pool(
                reroute, nodes, xs, ys, ix, iy, allowed,
                synth_samples, direction_seed + index * 7919,
            )
            for candidate in generated:
                if candidates_contact(fixed, candidate):
                    continue
                if fixed_rid == route_a:
                    pair = (fixed, candidate)
                else:
                    pair = (candidate, fixed)
                synthesized.append(pair)

    # Geometry pair identity dedupe, cheapest first.
    unique = {}
    for first, second in [*direct_pairs, *synthesized]:
        key = (first.points, second.points)
        score = first.cost + second.cost
        old = unique.get(key)
        if old is None or score < old[0]:
            unique[key] = (score, first, second)
    ranked = sorted(unique.values(), key=lambda item: (item[0], item[1].key, item[2].key))

    topology = topology_gate(plan)
    payload = {
        "status": "PASS" if ranked else "FAIL",
        "meaning": (
            "PASS proves only pairwise separability for this port plan and sampled family search; "
            "it does not prove a global 18-route embedding."
        ),
        "plan": plan,
        "topologyGateStatus": topology["status"],
        "orientableGenus": topology["orientableGenus"],
        "routeA": route_a,
        "routeB": route_b,
        "baseSamples": base_samples,
        "synthSamplesPerFixedCandidate": synth_samples,
        "fixedCandidateLimitPerDirection": fixed_limit,
        "basePoolCounts": {route_a: len(pool_a), route_b: len(pool_b)},
        "directCompatiblePairCount": len(direct_pairs),
        "synthesizedCompatiblePairCount": len(synthesized),
        "uniqueCompatiblePairCount": len(ranked),
        "examples": [
            {
                "totalCost": score,
                route_a: {
                    "family": first.family,
                    "cost": first.cost,
                    "points": [[x / 200.0, y / 200.0] for x, y in first.points],
                },
                route_b: {
                    "family": second.family,
                    "cost": second.cost,
                    "points": [[x / 200.0, y / 200.0] for x, y in second.points],
                },
            }
            for score, first, second in ranked[:20]
        ],
        "authoritativeCandidateModified": False,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if payload["status"] == "PASS" else 2


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--plan", default="PLAN_TRAVELER_SKELETON_PLANAR_GRID")
    parser.add_argument("--route-a", required=True)
    parser.add_argument("--route-b", required=True)
    parser.add_argument("--base-samples", type=int, default=12)
    parser.add_argument("--synth-samples", type=int, default=8)
    parser.add_argument("--fixed-limit", type=int, default=6)
    parser.add_argument("--seed", type=int, default=20260908)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    return run(**vars(args))


if __name__ == "__main__":
    raise SystemExit(main())
