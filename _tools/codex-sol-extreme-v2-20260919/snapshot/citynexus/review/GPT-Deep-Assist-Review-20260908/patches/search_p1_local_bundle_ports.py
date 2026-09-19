#!/usr/bin/env python3
"""Topology-safe local port search for the current P1 hard-route bundle.

This is a diagnostic/staging helper, not a promotion tool.  It searches a
small set of target-port variants for the repeatedly failing UC-06 / UC-07
cluster, generates diversified rectilinear candidate families, repairs
pairwise gaps, enforces AC-3, and finally asks the exact non-OR-Tools CSP
selector for one contact-free candidate per local route.

The three C4E1 Extend routes remain hard immutable obstacles.  A previously
validated Traveler skeleton may be supplied; matching routes are injected as
*optional candidates*, never frozen.  This retains proven good geometry while
still allowing the solver to rip it up when provider access requires that.

No authoritative YAML is modified.  A PASS is only a local witness and must be
re-integrated into a full 18-Association genus-0 search before V1/V2/V3.
"""
from __future__ import annotations

import argparse
import copy
import itertools
import json
import math
import sys
import time
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent), str(HERE)]

from explore_p1_disjoint_pool import (  # noqa: E402
    _candidate_pool,
    _merge_candidate,
    _repair_arc_empty_routes,
    _repair_pairwise_gaps,
)
from route_candidate_selector import (  # noqa: E402
    arc_consistency_prune,
    build_conflicts,
    find_first_solution,
    make_candidate,
    route_pair_compatibility,
)
from route_p1_negotiated_grid import build_axes, build_graph, load  # noqa: E402
from routing_geometry import route_points  # noqa: E402
from search_p1_global_port_rotations import genus, target_options  # noqa: E402

DEFAULT_PLAN = "PLAN_TRAVELER_SKELETON_PLANAR_GRID"
DEFAULT_BUNDLE = (
    "A-T-UC-06",
    "A-T-UC-07",
    "A-T-UC-11",
    "A-B-06",
    "A-PA-07",
)
VARY_ROUTE_TARGET = {
    "A-T-UC-06": "UC-06",
    "A-B-06": "UC-06",
    "A-PA-07": "UC-07",
}


def _nearest_options(node, *, include_left=False):
    options = target_options(node)
    sides = ("RIGHT", "TOP", "BOTTOM", "LEFT") if include_left else ("RIGHT", "TOP", "BOTTOM")
    wanted = (0.20, 0.50, 0.80)
    out = []
    for side in sides:
        side_values = [item for item in options if item[0] == side]
        for target in wanted:
            item = min(side_values, key=lambda value: abs(float(value[1]) - target))
            if item not in out:
                out.append(item)
    return out


def _port_signature(route):
    return (
        route["sourceSide"], round(float(route["sourcePortFraction"]), 12),
        route["targetSide"], round(float(route["targetPortFraction"]), 12),
    )


def _skeleton_candidate(route, nodes, skeleton_by_id):
    supplied = skeleton_by_id.get(route["id"])
    if not supplied or not supplied.get("waypoints"):
        return None
    # A skeleton geometry is valid only for exactly the same endpoint ports.
    if _port_signature(route) != _port_signature(supplied):
        return None
    points = route_points(supplied, nodes)
    try:
        return make_candidate({
            "routeId": route["id"],
            "family": "validated-traveler-skeleton",
            "points": points,
            "cost": sum(abs(b[0]-a[0]) + abs(b[1]-a[1]) for a,b in zip(points, points[1:])),
            "tag": f"{route['id']}:validated-skeleton",
        })
    except ValueError:
        return None


def _variant_score(base_routes, variant_routes):
    # Lower score first.  Prefer ports on the geometrically natural provider
    # side and fewer deviations from the validated genus-0 seed.
    score = 0.0
    for rid in VARY_ROUTE_TARGET:
        before = base_routes[rid]
        after = variant_routes[rid]
        if (before["targetSide"], float(before["targetPortFraction"])) != (
            after["targetSide"], float(after["targetPortFraction"])
        ):
            score += 1.0
        if rid in {"A-B-06", "A-PA-07"} and after["targetSide"] != "RIGHT":
            score += 0.35
        score += abs(float(after["targetPortFraction"]) - 0.5) * 0.05
    # Distinct UC-06 sides are useful because frozen EXT-07-06 creates a
    # narrow U-shaped obstacle around that node.
    if variant_routes["A-T-UC-06"]["targetSide"] == variant_routes["A-B-06"]["targetSide"]:
        score += 0.4
    return score


def _strategic_variants(base_routes, nodes, max_variants, vary_source=False, include_left=False):
    option_map = {}
    for rid, nid in VARY_ROUTE_TARGET.items():
        values = _nearest_options(nodes[nid], include_left=include_left)
        current = (base_routes[rid]["targetSide"], float(base_routes[rid]["targetPortFraction"]))
        if current not in values:
            values.insert(0, current)
        option_map[rid] = values

    # When the UC-06/07 corridor remains AC-3 empty, source-port allocation
    # on the Traveler actor is the next discrete degree of freedom.  Keep it
    # opt-in so the normal bounded search remains reproducible and cheap.
    source_ids = ("A-T-UC-06", "A-T-UC-07", "A-T-UC-11") if vary_source else ()
    source_values = {}
    if vary_source:
        # The actor's mutable right-side lanes are spaced at 0.10 increments;
        # include the current value and nearby alternatives.  Full genus
        # filtering below rejects collisions with the other Traveler routes.
        for rid in source_ids:
            current = float(base_routes[rid]["sourcePortFraction"])
            # Keep the Cartesian product bounded: five nearby lanes per
            # source route are enough to explore the local corridor while
            # avoiding millions of equivalent rotations.
            vals = [current] + [round(current + delta, 2) for delta in (-0.20, -0.10, 0.10, 0.20)
                                if 0.05 <= current + delta <= 0.95]
            source_values[rid] = list(dict.fromkeys(vals))

    rows = []
    products = itertools.product(*(option_map[rid] for rid in VARY_ROUTE_TARGET))
    for choices in products:
        routes = copy.deepcopy(base_routes)
        for rid, option in zip(VARY_ROUTE_TARGET, choices):
            routes[rid]["targetSide"], routes[rid]["targetPortFraction"] = option
        # Two connectors may not occupy the same perimeter position on UC-06.
        if (
            routes["A-T-UC-06"]["targetSide"] == routes["A-B-06"]["targetSide"]
            and abs(float(routes["A-T-UC-06"]["targetPortFraction"]) - float(routes["A-B-06"]["targetPortFraction"])) < 1e-9
        ):
            continue
        source_products = itertools.product(*(source_values[rid] for rid in source_ids)) if vary_source else [()]
        for source_choices in source_products:
            candidate = copy.deepcopy(routes)
            for rid, fraction in zip(source_ids, source_choices):
                candidate[rid]["sourcePortFraction"] = fraction
            g = genus(candidate, nodes)
            if g is None or abs(float(g)) > 1e-9:
                continue
            score = _variant_score(base_routes, candidate)
            score += sum(abs(float(candidate[rid]["sourcePortFraction"]) - float(base_routes[rid]["sourcePortFraction"])) for rid in source_ids) * 0.02
            rows.append((score, candidate))
    rows.sort(key=lambda item: item[0])
    return rows[:max_variants]


def _domain_summary(ac3):
    return {rid: len(values) for rid, values in ac3.get("domains", {}).items()}


def search(*, plan, skeleton, variants, samples, pair_rounds, pair_samples,
           pair_fixed, arc_rounds, arc_samples, arc_bundles, seed, seconds,
           checkpoint=None, vary_source=False, include_left=False):
    sem, original, nodes, base_routes, overrides, frozen, mutable = load(plan)
    skeleton_by_id = {}
    if skeleton:
        document = yaml.safe_load(Path(skeleton).read_text(encoding="utf-8")) or {}
        skeleton_by_id = {item.get("id"): item for item in document.get("routes", [])}

    variant_rows = _strategic_variants(base_routes, nodes, variants,
                                       vary_source=vary_source,
                                       include_left=include_left)
    start = time.monotonic()
    attempts = []
    best = None

    def write_checkpoint():
        if checkpoint is None:
            return
        payload = {
            "status": "RUNNING",
            "scope": "LOCAL_5_ROUTE_DIAGNOSTIC",
            "plan": plan,
            "bundle": list(DEFAULT_BUNDLE),
            "testedVariants": len(attempts),
            "elapsedSeconds": time.monotonic() - start,
            "bestAttempt": best[1] if best else None,
            "attempts": attempts,
        }
        Path(checkpoint).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    for index, (port_score, routes) in enumerate(variant_rows, 1):
        if time.monotonic() - start >= seconds:
            break
        local_routes = [routes[rid] for rid in DEFAULT_BUNDLE]
        xs, ys = build_axes(sem, local_routes, nodes, frozen)
        ix, iy, allowed = build_graph(xs, ys, nodes, frozen)
        pools = {}
        for rid in DEFAULT_BUNDLE:
            route_seed = seed + index * 100003 + sum(ord(ch) for ch in rid) * 101
            bucket = _candidate_pool(
                routes[rid], nodes, xs, ys, ix, iy, allowed, samples, route_seed,
            )
            skeleton_candidate = _skeleton_candidate(routes[rid], nodes, skeleton_by_id)
            if skeleton_candidate is not None:
                _merge_candidate(bucket, skeleton_candidate)
            pools[rid] = bucket

        pair_history = _repair_pairwise_gaps(
            pools=pools, routes=local_routes, nodes=nodes, xs=xs, ys=ys,
            frozen=frozen, rounds=pair_rounds, synth_samples=pair_samples,
            fixed_limit=pair_fixed, seed=seed + index * 7919,
        )
        conflicts = build_conflicts(pools)
        pair_rows = route_pair_compatibility(pools, conflicts=conflicts)
        impossible = [
            [row["routeA"], row["routeB"]]
            for row in pair_rows if row["compatiblePairs"] == 0
        ]
        ac3 = arc_consistency_prune(pools, conflicts=conflicts)
        arc_history = []
        if not impossible and ac3["status"] != "PASS" and arc_rounds > 0:
            arc_history = _repair_arc_empty_routes(
                pools=pools, routes=local_routes, nodes=nodes, xs=xs, ys=ys,
                frozen=frozen, rounds=arc_rounds, synth_samples=arc_samples,
                bundle_limit=arc_bundles, seed=seed + index * 104729,
            )
            conflicts = build_conflicts(pools)
            ac3 = arc_consistency_prune(pools, conflicts=conflicts)

        attempt = {
            "index": index,
            "portScore": port_score,
            "orientableGenus": 0.0,
            "portOverrides": {
                rid: {
                    "targetSide": routes[rid]["targetSide"],
                    "targetPortFraction": routes[rid]["targetPortFraction"],
                }
                for rid in VARY_ROUTE_TARGET
            },
            "candidateCounts": {rid: len(pools[rid]) for rid in DEFAULT_BUNDLE},
            "impossibleRoutePairs": impossible,
            "ac3Status": ac3["status"],
            "ac3EmptyRoutes": list(ac3.get("emptyRoutes", [])),
            "ac3DomainSizes": _domain_summary(ac3),
            "pairRepair": pair_history,
            "arcRepair": arc_history,
        }
        rank = (
            len(impossible),
            len(attempt["ac3EmptyRoutes"]),
            -sum(attempt["ac3DomainSizes"].values()),
            port_score,
        )
        if best is None or rank < best[0]:
            best = (rank, copy.deepcopy(attempt))

        if not impossible and ac3["status"] == "PASS":
            result = find_first_solution(
                ac3["domains"], conflicts=conflicts,
                time_limit_seconds=max(0.1, min(15.0, seconds - (time.monotonic() - start))),
            )
            attempt["selector"] = {
                key: value for key, value in result.items() if key != "selection"
            }
            if result["status"] == "PASS":
                attempt["selection"] = {
                    rid: {
                        "family": candidate.family,
                        "cost": candidate.cost,
                        "points": [[x / 200.0, y / 200.0] for x, y in candidate.points],
                    }
                    for rid, candidate in result["selection"].items()
                }
                attempts.append(attempt)
                payload = {
                    "status": "PASS",
                    "scope": "LOCAL_5_ROUTE_WITNESS_ONLY",
                    "plan": plan,
                    "bundle": list(DEFAULT_BUNDLE),
                    "testedVariants": index,
                    "elapsedSeconds": time.monotonic() - start,
                    "winner": attempt,
                    "attempts": attempts,
                    "warning": "Local witness only; full 18-Association topology/V1/V2/V3 still required.",
                }
                if checkpoint is not None:
                    Path(checkpoint).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
                return payload
        attempts.append(attempt)
        write_checkpoint()

    return {
        "status": "FAIL",
        "scope": "LOCAL_5_ROUTE_DIAGNOSTIC",
        "plan": plan,
        "bundle": list(DEFAULT_BUNDLE),
        "testedVariants": len(attempts),
        "elapsedSeconds": time.monotonic() - start,
        "bestAttempt": best[1] if best else None,
        "attempts": attempts,
        "nextAction": (
            "Broaden target/source port search for the AC-3-empty route(s), then regenerate bundle families; "
            "do not spend CP-SAT time on a pool that fails pairwise or AC-3 prechecks."
        ),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--plan", default=DEFAULT_PLAN)
    parser.add_argument("--traveler-skeleton", type=Path)
    parser.add_argument("--variants", type=int, default=30)
    parser.add_argument("--samples", type=int, default=4)
    parser.add_argument("--pair-repair-rounds", type=int, default=1)
    parser.add_argument("--pair-synth-samples", type=int, default=3)
    parser.add_argument("--pair-fixed-limit", type=int, default=3)
    parser.add_argument("--arc-repair-rounds", type=int, default=1)
    parser.add_argument("--arc-synth-samples", type=int, default=4)
    parser.add_argument("--arc-bundle-limit", type=int, default=12)
    parser.add_argument("--seed", type=int, default=20260908)
    parser.add_argument("--seconds", type=float, default=120.0)
    parser.add_argument("--vary-source", action="store_true",
                        help="also search Traveler source-port fractions")
    parser.add_argument("--include-left", action="store_true",
                        help="include LEFT target-side lanes in strategic search")
    parser.add_argument("--json-out", type=Path)
    args = parser.parse_args()
    payload = search(
        plan=args.plan, skeleton=args.traveler_skeleton,
        variants=args.variants, samples=args.samples,
        pair_rounds=args.pair_repair_rounds, pair_samples=args.pair_synth_samples,
        pair_fixed=args.pair_fixed_limit,
        arc_rounds=args.arc_repair_rounds, arc_samples=args.arc_synth_samples,
        arc_bundles=args.arc_bundle_limit,
        seed=args.seed, seconds=args.seconds, checkpoint=args.json_out,
        vary_source=args.vary_source, include_left=args.include_left,
    )
    text = json.dumps(payload, ensure_ascii=False, indent=2)
    print(text)
    if args.json_out:
        args.json_out.write_text(text, encoding="utf-8")
    return 0 if payload["status"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
