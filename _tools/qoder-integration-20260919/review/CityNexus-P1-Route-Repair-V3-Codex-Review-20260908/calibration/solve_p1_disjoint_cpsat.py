"""Exact multi-commodity rectilinear routing search for P1 Associations.

Each Association receives a simple path over a fixed 0.10-cm turn-event grid.
CP-SAT enforces capacity one at every grid vertex, so perpendicular crossings,
T junctions, shared bends, and collinear overlaps are all excluded before a
candidate is written.  Shape interiors and the three frozen Extend routes are
already omitted from the graph by the shared geometry predicate.
"""
from __future__ import annotations

import argparse
import copy
import json
import sys
from collections import deque
from pathlib import Path

import yaml
from ortools.sat.python import cp_model

HERE = Path(__file__).resolve().parent
RENDERER = HERE.parent
sys.path[:0] = [str(RENDERER), str(HERE)]

from plan_p1_associations import FROZEN, compact  # noqa: E402
from route_p1_negotiated_grid import (  # noqa: E402
    STAGING, TRACE, build_axes, build_graph, load, terminal_scaffold,
)
from routing_geometry import route_points  # noqa: E402


def build_instance(plan_id, traveler_skeleton=None, only_family=None):
    sem, original, nodes, routes, overrides, frozen, mutable = load(plan_id)
    skeleton_routes = {}
    if traveler_skeleton:
        document = yaml.safe_load(Path(traveler_skeleton).read_text(encoding="utf-8"))
        skeleton_routes = {route["id"]: route for route in document.get("routes", [])}
        for rid, supplied in skeleton_routes.items():
            if rid not in routes:
                continue
            # Port values come from the active topology plan so the skeleton
            # is represented with exact, orthogonal endpoint coordinates;
            # only its independently verified corridor waypoints are reused.
            routes[rid]["waypoints"] = copy.deepcopy(supplied["waypoints"])
            frozen[rid] = route_points(routes[rid], nodes)
        mutable = [route for route in mutable if route["id"] not in skeleton_routes]
    if only_family:
        mutable = [route for route in mutable if route.get("family") == only_family]
    xs, ys = build_axes(sem, mutable, nodes, frozen)
    ix, iy, allowed = build_graph(xs, ys, nodes, frozen)
    coords = [(x, y) for x in xs for y in ys]
    edges = []
    adjacency = {p: [] for p in coords}
    for i, x in enumerate(xs):
        for j, y in enumerate(ys):
            a = (x, y)
            for ni, nj in ((i + 1, j), (i, j + 1)):
                if ni >= len(xs) or nj >= len(ys):
                    continue
                b = (xs[ni], ys[nj])
                if allowed(a, b):
                    number = len(edges)
                    edges.append((a, b))
                    adjacency[a].append(number); adjacency[b].append(number)
    terminals = {}
    for route in mutable:
        _, start, goal, _, _, td = terminal_scaffold(route, nodes)
        terminals[route["id"]] = (start, goal, (-td[0], -td[1]))
        if start not in adjacency or goal not in adjacency:
            raise ValueError(f"terminal outside graph: {route['id']} {start} {goal}")
    return original, nodes, overrides, mutable, xs, ys, edges, adjacency, terminals, skeleton_routes


def solve(plan_id, seconds, workers, optimize, traveler_skeleton=None, only_family=None):
    original, nodes, overrides, routes, xs, ys, edges, adjacency, terminals, skeleton_routes = build_instance(plan_id, traveler_skeleton, only_family)
    model = cp_model.CpModel()
    route_vars = {}
    active_vars = {}
    occupancy = {}
    for route in routes:
        rid = route["id"]
        selected = [model.new_bool_var(f"{rid}_e{index}") for index in range(len(edges))]
        route_vars[rid] = selected
        start, goal, incoming = terminals[rid]
        for point, incident in adjacency.items():
            degree = sum(selected[e] for e in incident)
            if point == start or point == goal:
                model.add(degree == 1)
                occupancy[rid, point] = 1
            else:
                active = model.new_bool_var(f"{rid}_v_{point[0]}_{point[1]}")
                active_vars[rid, point] = active
                occupancy[rid, point] = active
                model.add(degree == 2 * active)
        # The final target segment must be tangent to its declared target side.
        allowed_last = []
        for e in adjacency[goal]:
            a, b = edges[e]
            other = b if a == goal else a
            direction = (goal[0] - other[0], goal[1] - other[1])
            if (direction[0] * incoming[0] > 0 or direction[1] * incoming[1] > 0) and (
                (incoming[0] == 0 or direction[1] == 0)
                and (incoming[1] == 0 or direction[0] == 0)
            ):
                allowed_last.append(e)
        if not allowed_last:
            raise ValueError(f"no tangential target approach: {rid}")
        for e in adjacency[goal]:
            if e not in allowed_last:
                model.add(selected[e] == 0)
        # Bound every route to a generous detour over its own shortest path.
        # It removes disconnected cycles from the feasibility search and
        # makes the joint solver focus on useful corridor choices.
        distance = {start: 0}
        queue = deque([start])
        while queue:
            point = queue.popleft()
            for e in adjacency[point]:
                a, b = edges[e]
                other = b if a == point else a
                if other not in distance:
                    distance[other] = distance[point] + 1
                    queue.append(other)
        last_lengths = []
        for e in allowed_last:
            a, b = edges[e]
            other = b if a == goal else a
            if other in distance:
                last_lengths.append(distance[other] + 1)
        if not last_lengths:
            raise ValueError(f"target direction disconnected: {rid}")
        model.add(sum(selected) <= min(last_lengths) + 30)
    # Vertex capacity one is the exact no-contact contract on this orthogonal
    # grid.  Endpoint ports are distinct by construction.
    for point, incident in adjacency.items():
        model.add(sum(occupancy[rid, point] for rid in route_vars) <= 1)
    if optimize:
        model.minimize(sum(var for selected in route_vars.values() for var in selected))
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = seconds
    solver.parameters.num_search_workers = workers
    solver.parameters.random_seed = 20260907
    solver.parameters.log_search_progress = False
    status = solver.solve(model)
    label = solver.status_name(status)
    payload = {
        "status": "PASS" if status in (cp_model.OPTIMAL, cp_model.FEASIBLE) else "FAIL",
        "solverStatus": label, "plan": plan_id,
        "axisCounts": {"x": len(xs), "y": len(ys)},
        "edgeCount": len(edges), "routeCount": len(routes),
        "wallTimeSeconds": solver.wall_time, "objective": solver.objective_value,
        "authoritativeCandidateModified": False, "frozenExtendIds": sorted(FROZEN),
    }
    if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        TRACE.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return payload
    paths = {}
    for route in routes:
        rid = route["id"]
        start, goal, _ = terminals[rid]
        selected = {idx for idx, var in enumerate(route_vars[rid]) if solver.boolean_value(var)}
        current, previous = start, None
        points = [start]
        while current != goal:
            choices = []
            for edge_index in adjacency[current]:
                if edge_index not in selected:
                    continue
                a, b = edges[edge_index]
                other = b if a == current else a
                if other != previous:
                    choices.append(other)
            if len(choices) != 1:
                raise RuntimeError(f"ambiguous selected path {rid} at {current}: {choices}")
            previous, current = current, choices[0]
            points.append(current)
            if len(points) > len(edges):
                raise RuntimeError(f"cycle extracted for {rid}")
        start_endpoint, _, _, goal_endpoint, _, _ = terminal_scaffold(route, nodes)
        paths[rid] = compact([start_endpoint, *points, goal_endpoint])
    staged = copy.deepcopy(original)
    staged["metadata"]["status"] = "STAGING_GEOMETRY_CANDIDATE"
    for route in staged["routes"]:
        rid = route["id"]
        supplied = skeleton_routes.get(rid)
        if supplied is not None:
            route.update(overrides.get(rid, {}))
            route["waypoints"] = copy.deepcopy(supplied["waypoints"])
            route["planningStatus"] = "ROUTE_PLANNED_PENDING_EXTERNAL_FREEZE"
            continue
        if rid not in paths:
            continue
        route.update(overrides.get(rid, {}))
        route["waypoints"] = [[round(x, 2), round(y, 2)] for x, y in paths[rid][1:-1]]
        route["planningStatus"] = "ROUTE_PLANNED_PENDING_EXTERNAL_FREEZE"
    STAGING.write_text(yaml.safe_dump(staged, sort_keys=False), encoding="utf-8")
    payload["stagingCandidate"] = str(STAGING)
    TRACE.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return payload


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--plan", default="PLAN_O_GRID10_NEGOTIATED")
    parser.add_argument("--seconds", type=float, default=300.0)
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--optimize", action="store_true", help="minimize edge use after a feasible model is found")
    parser.add_argument("--traveler-skeleton", help="validated Traveler sub-solution to treat as fixed routing obstacle")
    parser.add_argument("--only-family", choices=("traveler", "provider"), help="route just one Association family against frozen Extends")
    args = parser.parse_args()
    result = solve(args.plan, args.seconds, args.workers, args.optimize, args.traveler_skeleton, args.only_family)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
