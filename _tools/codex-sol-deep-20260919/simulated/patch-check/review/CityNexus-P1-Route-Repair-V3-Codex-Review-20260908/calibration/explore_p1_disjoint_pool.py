"""Parallel-safe diversified candidate-pool search for P1 Associations.

The direct CP-SAT model assigns every grid edge to every commodity.  Its
multi-commodity flow constraints are exact but unnecessarily large for an
interactive repair loop.  This helper first samples many *simple, legal*
rectilinear paths per route on the same grid, then asks CP-SAT to select one
contact-free path for every route.  Individual runs never write the shared
staging candidate; that makes independent seeds safe to run concurrently.
"""
from __future__ import annotations

import argparse
import copy
import heapq
import itertools
import json
import os
import random
import sys
from collections import Counter
from pathlib import Path

import yaml
from ortools.sat.python import cp_model

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent), str(HERE)]

from plan_p1_associations import FROZEN, compact  # noqa: E402
from route_candidate_selector import build_conflicts, make_candidate  # noqa: E402
from critical_grid_geometry import closed_contact, q  # noqa: E402
from route_p1_negotiated_grid import (  # noqa: E402
    STAGING, astar, build_axes, build_graph, load,
)
from routing_geometry import route_points  # noqa: E402


def _path_cost(points):
    length = sum(abs(b[0] - a[0]) + abs(b[1] - a[1]) for a, b in zip(points, points[1:]))
    bends = sum(
        (a[0] - b[0]) * (b[0] - c[0]) + (a[1] - b[1]) * (b[1] - c[1]) == 0
        for a, b, c in zip(points, points[1:], points[2:])
    )
    return length + bends * 0.35


def _field(xs, ys, seed, family):
    """Return non-negative history costs that explore a distinct homotopy.

    ``astar`` accepts historic congestion counters.  Here we deliberately use
    them as a reproducible terrain field.  The field never creates an illegal
    edge -- shape and frozen-Extend checks remain in ``build_graph`` -- but it
    makes a useful detour competitive with the local Manhattan shortest path.
    """
    rng = random.Random(seed)
    # Each named family gets an actual destination corridor.  The earlier
    # prototype chose a guide over the *whole* page for every family, which
    # accidentally made most "top" and "bottom" samples indistinguishable
    # from unrestricted local shortest paths.
    if family == "top":
        guide_y = rng.choice((0.5, 1.0, 1.5, 2.0, 2.5, 3.0))
        guide_x = rng.choice((5.0, 6.0, 7.0))
    elif family == "bottom":
        guide_y = rng.choice((16.0, 16.5, 17.0, 17.5, 18.0, 18.5))
        guide_x = rng.choice((5.0, 6.0, 7.0))
    elif family == "left":
        guide_y = rng.choice((3.0, 5.0, 7.0, 9.0, 11.0, 13.0, 15.0, 17.0))
        guide_x = rng.choice((4.5, 5.0, 5.5, 6.0, 6.5, 7.0))
    elif family == "right":
        guide_y = rng.choice((2.0, 4.0, 6.0, 8.0, 10.0, 12.0, 14.0, 16.0, 18.0))
        guide_x = rng.choice((27.0, 27.5, 28.0, 28.5, 29.0, 29.5))
    else:
        guide_y = rng.choice((1.0, 3.0, 5.0, 7.0, 9.0, 11.0, 13.0, 15.0, 17.0, 18.0))
        guide_x = rng.choice((5.0, 6.0, 7.0, 14.0, 20.0, 27.0, 28.0, 29.0))
    scale = 0.30 + rng.random() * 0.65
    jitter = 0.03 + rng.random() * 0.08
    vertices = Counter()
    edges = Counter()
    for x in xs:
        for y in ys:
            guide = 0.0
            if family == "top":
                guide = max(0.0, y - guide_y) * scale
            elif family == "bottom":
                guide = max(0.0, guide_y - y) * scale
            elif family == "left":
                guide = max(0.0, x - guide_x) * scale
            elif family == "right":
                guide = max(0.0, guide_x - x) * scale
            elif family == "cross":
                guide = min(abs(y - guide_y), abs(x - guide_x)) * scale
            # Coarse pseudo-random terrain changes ties and permits a route
            # to leave a preferred lane when an obstacle requires it.
            vertices[(x, y)] = guide + rng.random() * jitter
    return vertices, edges


def _candidate_pool(route, nodes, xs, ys, ix, iy, allowed, samples, seed):
    unique = {}
    families = ("free", "top", "bottom", "left", "right", "cross")
    for index in range(samples):
        family = families[index % len(families)]
        field, edge_field = _field(xs, ys, seed + index * 1009, family)
        path = astar(
            route, nodes, xs, ys, ix, iy, allowed,
            Counter(), Counter(), field, edge_field,
            0.0, 0.10 + (index % 5) * 0.20,
            random.Random(seed + index * 7919), noise=0.001,
        )
        if path is None:
            continue
        path = compact(path)
        try:
            candidate = make_candidate({
                "routeId": route["id"], "family": family,
                "points": path, "cost": _path_cost(path),
                "tag": f"{route['id']}:{index}",
            })
        except ValueError:
            continue
        # A compact polyline is the actual candidate identity.  Keep the
        # cheapest tag for duplicate geometry, otherwise CP-SAT gets no new
        # choice but pays a much larger presolve cost.
        old = unique.get(candidate.points)
        if old is None or candidate.cost < old.cost:
            unique[candidate.points] = candidate

        # A terrain field can make a detour attractive, but cannot guarantee
        # that it crosses a particular face.  Add an explicitly anchored
        # alternative in the same sample so the selector sees genuine outer
        # and side-corridor homotopies, not merely noisy variants of one
        # shortest path.
        # One explicit anchor sample per four terrain samples is enough to
        # seed each of the eight broad corridor patterns.  Keeping it sparse
        # is important: each anchored sample performs three constrained A*
        # searches, while all samples still get the cheap single-pass terrain
        # search above.
        anchors = _anchors(xs, ys, index // 4, seed) if index % 4 == 0 else None
        anchored = (
            _anchored_path(route, nodes, xs, ys, ix, iy, allowed, field, anchors)
            if anchors is not None else None
        )
        if anchored and _simple_polyline(anchored):
            anchored = compact(anchored)
            try:
                candidate = make_candidate({
                    "routeId": route["id"], "family": f"anchor-{index % 8}",
                    "points": anchored, "cost": _path_cost(anchored) + 1.0,
                    "tag": f"{route['id']}:a{index}",
                })
            except ValueError:
                continue
            old = unique.get(candidate.points)
            if old is None or candidate.cost < old.cost:
                unique[candidate.points] = candidate
    return sorted(unique.values(), key=lambda c: (c.cost, c.key))


def _anchors(xs, ys, index, seed):
    """Choose two concrete points for one broad outer/side homotopy."""
    rng = random.Random(seed + 44017)
    # All values are chosen from the event grid itself, so an anchor never
    # introduces a non-normalizable waypoint.
    left = [x for x in xs if 4.5 <= x <= 7.0]
    right = [x for x in xs if 27.0 <= x <= 29.5]
    top = [y for y in ys if 0.5 <= y <= 3.0]
    bottom = [y for y in ys if 16.0 <= y <= 18.5]
    middle = [y for y in ys if 3.0 <= y <= 16.0]
    pattern = index % 8
    if pattern in (0, 1):
        y = rng.choice(top)
        return ((rng.choice(left), y), (rng.choice(right), y))
    if pattern in (2, 3):
        y = rng.choice(bottom)
        return ((rng.choice(left), y), (rng.choice(right), y))
    if pattern == 4:
        x = rng.choice(left)
        return ((x, rng.choice(middle)), (x, rng.choice(middle)))
    if pattern == 5:
        x = rng.choice(right)
        return ((x, rng.choice(middle)), (x, rng.choice(middle)))
    if pattern == 6:
        return ((rng.choice(left), rng.choice(top)), (rng.choice(right), rng.choice(bottom)))
    return ((rng.choice(left), rng.choice(bottom)), (rng.choice(right), rng.choice(top)))


def _grid_path(start, goal, xs, ys, ix, iy, allowed, field, first=None, last=None):
    """Shortest legal grid segment with optional tangent directions."""
    if start[0] not in ix or start[1] not in iy or goal[0] not in ix or goal[1] not in iy:
        return None
    dirs = ((1, 0), (-1, 0), (0, 1), (0, -1))
    dindex = {direction: number for number, direction in enumerate(dirs)}
    start_state = (ix[start[0]], iy[start[1]], -1)
    queue = [(0.0, 0, start_state)]
    distance = {start_state: 0.0}
    parent = {start_state: None}
    serial = itertools.count(1)
    while queue:
        _, _, state = heapq.heappop(queue)
        x, y = xs[state[0]], ys[state[1]]
        current = (x, y)
        if current == goal and (last is None or state[2] == dindex[last]):
            result = []
            while state is not None:
                result.append((xs[state[0]], ys[state[1]]))
                state = parent[state]
            return list(reversed(result))
        for number, direction in enumerate(dirs):
            if state[2] == -1 and first is not None and direction != first:
                continue
            ni, nj = state[0] + direction[0], state[1] + direction[1]
            if not (0 <= ni < len(xs) and 0 <= nj < len(ys)):
                continue
            other = (xs[ni], ys[nj])
            if not allowed(current, other):
                continue
            length = abs(other[0] - current[0]) + abs(other[1] - current[1])
            bend = 0.25 if state[2] >= 0 and state[2] != number else 0.0
            cost = distance[state] + length + bend + field[other]
            next_state = (ni, nj, number)
            if cost + 1e-10 < distance.get(next_state, float("inf")):
                distance[next_state] = cost
                parent[next_state] = state
                heuristic = abs(other[0] - goal[0]) + abs(other[1] - goal[1])
                heapq.heappush(queue, (cost + heuristic, next(serial), next_state))
    return None


def _anchored_path(route, nodes, xs, ys, ix, iy, allowed, field, anchors):
    from route_p1_negotiated_grid import outward, terminal_scaffold

    start, start_stub, goal_stub, goal, source_direction, target_direction = terminal_scaffold(route, nodes)
    parts = []
    previous = start_stub
    for number, anchor in enumerate((*anchors, goal_stub)):
        portion = _grid_path(
            previous, anchor, xs, ys, ix, iy, allowed, field,
            first=source_direction if number == 0 else None,
            last=(-target_direction[0], -target_direction[1]) if anchor == goal_stub else None,
        )
        if portion is None:
            return None
        parts.extend(portion if not parts else portion[1:])
        previous = anchor
    return [start, *parts, goal]


def _simple_polyline(points):
    """Reject a self-contact introduced by joining independently routed legs."""
    segments = list(zip(points, points[1:]))
    for number, (a, b) in enumerate(segments):
        qa, qb = (q(a[0]), q(a[1])), (q(b[0]), q(b[1]))
        for other, (c, d) in enumerate(segments[number + 1:], number + 1):
            if other <= number + 1:
                continue
            qc, qd = (q(c[0]), q(c[1])), (q(d[0]), q(d[1]))
            if closed_contact(qa, qb, qc, qd):
                return False
    return True


def _select(pools, seconds, workers, seed):
    conflicts = build_conflicts(pools)
    flat = [candidate for values in pools.values() for candidate in values]
    model = cp_model.CpModel()
    selected = {candidate.key: model.new_bool_var(f"c{number}") for number, candidate in enumerate(flat)}
    for values in pools.values():
        model.add_exactly_one(selected[candidate.key] for candidate in values)
    pairs = set()
    for key, blocked in conflicts.items():
        for other in blocked:
            pair = tuple(sorted((key, other)))
            if pair in pairs:
                continue
            pairs.add(pair)
            model.add(selected[key] + selected[other] <= 1)
    model.minimize(sum(selected[candidate.key] * round(candidate.cost * 100) for candidate in flat))
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = seconds
    solver.parameters.num_search_workers = workers
    solver.parameters.random_seed = seed
    status = solver.solve(model)
    picked = {}
    partial = {}
    if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        for rid, values in pools.items():
            picked[rid] = next(candidate for candidate in values if solver.boolean_value(selected[candidate.key]))
    elif status == cp_model.INFEASIBLE:
        # Keep an actionable maximal no-contact subset.  It is a diagnostic
        # only: an omitted route is never silently promoted.  The result tells
        # the next rip-up round exactly which nets need new homotopies.
        relaxed = cp_model.CpModel()
        choose = {candidate.key: relaxed.new_bool_var(f"r{number}") for number, candidate in enumerate(flat)}
        active = {}
        for rid, values in pools.items():
            flag = relaxed.new_bool_var(f"active_{rid}")
            active[rid] = flag
            relaxed.add(sum(choose[candidate.key] for candidate in values) == flag)
        for first, second in pairs:
            relaxed.add(choose[first] + choose[second] <= 1)
        relaxed.maximize(sum(active.values()) * 100000 - sum(choose[c.key] * round(c.cost * 10) for c in flat))
        partial_solver = cp_model.CpSolver()
        partial_solver.parameters.max_time_in_seconds = min(seconds, 30.0)
        partial_solver.parameters.num_search_workers = workers
        partial_solver.parameters.random_seed = seed
        partial_solver.solve(relaxed)
        for rid, values in pools.items():
            candidate = next((c for c in values if partial_solver.boolean_value(choose[c.key])), None)
            if candidate is not None:
                partial[rid] = candidate
    return solver, status, picked, len(pairs), partial


def run(plan, samples, seconds, workers, seed, output, write_staging, only_family, fixed_routes, export_routes):
    sem, original, nodes, routes, overrides, frozen, mutable = load(plan)
    fixed = {}
    if fixed_routes:
        supplied = yaml.safe_load(fixed_routes.read_text(encoding="utf-8")) or {}
        for supplied_route in supplied.get("routes", []):
            rid = supplied_route.get("id")
            if rid not in routes or not supplied_route.get("waypoints"):
                continue
            routes[rid]["waypoints"] = copy.deepcopy(supplied_route["waypoints"])
            fixed[rid] = copy.deepcopy(routes[rid])
            frozen[rid] = route_points(routes[rid], nodes)
    mutable = [route for route in mutable if route["id"] not in fixed]
    if only_family:
        mutable = [route for route in mutable if route.get("family") == only_family]
    xs, ys = build_axes(sem, mutable, nodes, frozen)
    ix, iy, allowed = build_graph(xs, ys, nodes, frozen)
    pools = {}
    for route in mutable:
        route_seed = seed + sum(ord(ch) for ch in route["id"]) * 100003
        pools[route["id"]] = _candidate_pool(
            route, nodes, xs, ys, ix, iy, allowed, samples, route_seed,
        )
    # The handoff skeleton is an explicitly validated Traveler *sub-solution*
    # and is legal only on the matching port seed.  Include it as one candidate
    # rather than freezing it globally; CP-SAT may still choose a different
    # route if a future plan provides a better disjoint embedding.
    skeleton_path = HERE.parent.parent.parent / "handoff_20260907" / "traveler-corridor-skeleton.yaml"
    if plan in ("PLAN_TRAVELER_SKELETON_PROVIDER_GRID", "PLAN_TRAVELER_SKELETON_PLANAR_GRID") and skeleton_path.exists():
        document = yaml.safe_load(skeleton_path.read_text(encoding="utf-8")) or {}
        supplied_by_id = {item.get("id"): item for item in document.get("routes", [])}
        for route in mutable:
            supplied = supplied_by_id.get(route["id"])
            if supplied is None or route.get("family") != "traveler":
                continue
            with_skeleton = copy.deepcopy(route)
            with_skeleton["waypoints"] = copy.deepcopy(supplied.get("waypoints", []))
            try:
                skeleton_candidate = make_candidate({
                    "routeId": route["id"], "family": "validated-skeleton",
                    "points": route_points(with_skeleton, nodes),
                    "cost": _path_cost(route_points(with_skeleton, nodes)),
                    "tag": f"{route['id']}:validated-skeleton",
                })
            except (KeyError, ValueError):
                continue
            pools[route["id"]].append(skeleton_candidate)
    empty = sorted(rid for rid, values in pools.items() if not values)
    payload = {
        "status": "FAIL", "plan": plan, "seed": seed,
        "samples": samples, "axisCounts": {"x": len(xs), "y": len(ys)},
        "familyCounts": {rid: len(values) for rid, values in pools.items()},
        "emptyRoutes": empty, "authoritativeCandidateModified": False,
        "frozenExtendIds": sorted(FROZEN),
        "pid": os.getpid(),
    }
    if not empty:
        solver, status, picked, pairs, partial = _select(pools, seconds, workers, seed)
        payload.update({
            "solverStatus": solver.status_name(status), "wallTimeSeconds": solver.wall_time,
            "candidateCount": sum(len(values) for values in pools.values()),
            "conflictPairCount": pairs,
        })
        if partial:
            payload["maximalDisjointSubset"] = sorted(partial)
            payload["missingFromMaximalSubset"] = sorted(set(pools) - set(partial))
        if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            payload["status"] = "PASS"
            payload["selection"] = {rid: candidate.key for rid, candidate in picked.items()}
            payload["selectionPaths"] = {
                rid: [[round(x / 200, 2), round(y / 200, 2)] for x, y in candidate.points]
                for rid, candidate in picked.items()
            }
            if export_routes:
                exported = {"metadata": {"plan": plan, "seed": seed}, "routes": []}
                for rid, candidate in picked.items():
                    route = copy.deepcopy(routes[rid])
                    route["waypoints"] = [[round(x / 200, 2), round(y / 200, 2)] for x, y in candidate.points[1:-1]]
                    exported["routes"].append(route)
                export_routes.parent.mkdir(parents=True, exist_ok=True)
                export_routes.write_text(yaml.safe_dump(exported, sort_keys=False), encoding="utf-8")
                payload["exportedRoutes"] = str(export_routes)
            if write_staging:
                staged = copy.deepcopy(original)
                staged["metadata"]["status"] = "STAGING_GEOMETRY_CANDIDATE"
                for route in staged["routes"]:
                    candidate = picked.get(route["id"])
                    if candidate is None:
                        continue
                    route.update(overrides.get(route["id"], {}))
                    route["waypoints"] = [[round(x / 200, 2), round(y / 200, 2)] for x, y in candidate.points[1:-1]]
                    route["planningStatus"] = "ROUTE_PLANNED_PENDING_EXTERNAL_FREEZE"
                STAGING.write_text(yaml.safe_dump(staged, sort_keys=False), encoding="utf-8")
                payload["stagingCandidate"] = str(STAGING)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if payload["status"] == "PASS" else 2


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--plan", default="PLAN_O_GRID10_NEGOTIATED")
    parser.add_argument("--samples", type=int, default=80)
    parser.add_argument("--seconds", type=float, default=120.0)
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--seed", type=int, default=20260907)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--write-staging", action="store_true")
    parser.add_argument("--only-family", choices=("traveler", "provider"))
    parser.add_argument("--fixed-routes", type=Path, help="routes to treat as immutable obstacles for this isolated run")
    parser.add_argument("--export-routes", type=Path, help="write the selected subset for a later isolated experiment")
    args = parser.parse_args()
    raise SystemExit(run(**vars(args)))


if __name__ == "__main__":
    main()
