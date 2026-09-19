"""Negotiated-congestion router for the complete P1 Association set.

The historical workbench generated one local shortest path per corridor
family.  That is insufficient for this page: several locally shortest routes
form barriers that only disappear when every mutable route is ripped up and
rerouted together.  This module implements the classic PathFinder loop over a
rectilinear critical grid.  The three frozen Extend polylines and every shape
interior are immutable hard obstacles; Association occupancy is negotiated
through present and historical congestion costs.

This is a staging tool.  It writes only calibration/out/P1-STAGING-CANDIDATE.
yaml and a JSON trace.  Promotion is performed separately after V1/V2/V3 and
the full test suite pass.
"""
from __future__ import annotations

import argparse
import copy
import heapq
import itertools
import json
import math
import random
import sys
import time
from collections import Counter
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
RENDERER = HERE.parent
ROOT = RENDERER.parent
sys.path.insert(0, str(RENDERER))
sys.path.insert(0, str(HERE))

from critical_grid_geometry import closed_contact, q  # noqa: E402
from routing_geometry import node_box, route_points, segment_intersects_box_interior, side_port  # noqa: E402
from plan_p1_associations import CANDIDATE, FROZEN, PLAN_FILE, SEMANTIC, compact  # noqa: E402
from route_candidate_selector import CandidateError, build_conflicts, make_candidate  # noqa: E402
from audit_p1_route_topology_v2 import require_planar_topology  # noqa: E402

OUT = HERE / "out"
TRACE = OUT / "P1-NEGOTIATED-GRID-TRACE.json"
STAGING = OUT / "P1-STAGING-CANDIDATE.yaml"

_TOPOLOGY_CACHE = {}

def topology_gate(plan_id):
    payload = _TOPOLOGY_CACHE.get(plan_id)
    if payload is None:
        payload = require_planar_topology(
            semantic=SEMANTIC, candidate=CANDIDATE, plans=PLAN_FILE, plan=plan_id,
        )
        _TOPOLOGY_CACHE[plan_id] = payload
    return payload


def _resolve_plan(plans, plan_id, seen=()):
    if plan_id in seen:
        raise ValueError("cyclic plan inheritance")
    plan = plans[plan_id]
    out = _resolve_plan(plans, plan["basePlan"], (*seen, plan_id)) if plan.get("basePlan") else {}
    out.update(copy.deepcopy(plan.get("routes", {})))
    return out


def load(plan_id):
    # Central safety interlock: every solver that imports this loader must
    # reject a non-planar endpoint rotation before any path search begins.
    # This prevents hours of search on genus>0 port plans.
    topology_gate(plan_id)
    sem = yaml.safe_load(SEMANTIC.read_text(encoding="utf-8"))
    original = yaml.safe_load(CANDIDATE.read_text(encoding="utf-8"))
    plans = yaml.safe_load(PLAN_FILE.read_text(encoding="utf-8"))["plans"]
    overrides = _resolve_plan(plans, plan_id)
    nodes = {s["id"]: s for s in sem["shapes"] if s["id"] != "BOUNDARY"}
    routes = {r["id"]: copy.deepcopy(r) for r in original["routes"]}
    for rid, values in overrides.items():
        routes[rid].update(values)
    frozen = {rid: route_points(routes[rid], nodes) for rid in FROZEN}
    mutable = [r for r in routes.values() if r["connectorType"] == "association"]
    return sem, original, nodes, routes, overrides, frozen, mutable


def endpoint(route, nodes, which):
    node = nodes[route[which]]
    side = route[which + "Side"]
    fraction = route[which + "PortFraction"]
    p = side_port(node, side, fraction)
    return (round(float(p[0]), 3), round(float(p[1]), 3))


def outward(side):
    return {"LEFT": (-1, 0), "RIGHT": (1, 0), "TOP": (0, -1), "BOTTOM": (0, 1)}[side]


def terminal_scaffold(route, nodes):
    """Return exact endpoints and legal two-decimal exterior stubs."""
    start = endpoint(route, nodes, "source")
    goal = endpoint(route, nodes, "target")
    sd = outward(route["sourceSide"])
    td = outward(route["targetSide"])
    # Use the first legal 0.10-cm clearance point outside each actor.  A
    # shared deep fan-out line artificially welded otherwise independent
    # ports into a barrier, which is precisely the deadlock this global
    # router replaces.
    start_stub = (round(start[0] + sd[0] * 0.10, 2), round(start[1] + sd[1] * 0.10, 2))
    goal_stub = (round(goal[0] + td[0] * 0.10, 2), round(goal[1] + td[1] * 0.10, 2))
    if abs(start_stub[0] - round(start_stub[0], 2)) > 1e-8 or abs(start_stub[1] - round(start_stub[1], 2)) > 1e-8:
        raise ValueError(f"non-normalizable source stub {route['id']}: {start_stub}")
    if abs(goal_stub[0] - round(goal_stub[0], 2)) > 1e-8 or abs(goal_stub[1] - round(goal_stub[1], 2)) > 1e-8:
        raise ValueError(f"non-normalizable target stub {route['id']}: {goal_stub}")
    return start, start_stub, goal_stub, goal, sd, td


def build_axes(sem, mutable, nodes, frozen):
    # Sparse turn-event projection: shape/frozen/terminal coordinates and
    # their exact 0.10-cm clearance lanes, plus broad 1-cm escape corridors.
    width, height = float(sem["pageWidth"]), float(sem["pageHeight"])
    raw_x = {0.0, math.floor(width * 10) / 10, *(i / 2 for i in range(1, int(width * 2)))}
    raw_y = {0.0, math.floor(height * 10) / 10, *(i / 2 for i in range(1, int(height * 2)))}
    for node in nodes.values():
        box = node_box(node)
        raw_x.update((box.left - 0.10, box.right + 0.10))
        raw_y.update((box.top - 0.10, box.bottom + 0.10))
    for points in frozen.values():
        for x, y in points:
            raw_x.add(float(x)); raw_y.add(float(y))

    xs = {round(v, 1) for v in raw_x if 0.0 <= v <= width}
    ys = {round(v, 1) for v in raw_y if 0.0 <= v <= height}
    for route in mutable:
        _, s, g, _, _, _ = terminal_scaffold(route, nodes)
        xs.update((s[0], g[0])); ys.update((s[1], g[1]))
    return sorted(xs), sorted(ys)


def build_graph(xs, ys, nodes, frozen):
    ix = {x: i for i, x in enumerate(xs)}
    iy = {y: i for i, y in enumerate(ys)}
    boxes = tuple(node_box(n) for n in nodes.values())
    frozen_segments = [
        (tuple(q(v) for v in a), tuple(q(v) for v in b))
        for pts in frozen.values() for a, b in zip(pts, pts[1:])
    ]
    cache = {}

    def allowed(a, b):
        key = (a, b) if a <= b else (b, a)
        hit = cache.get(key)
        if hit is not None:
            return hit
        ok = not any(segment_intersects_box_interior(a, b, box) for box in boxes)
        if ok:
            qa, qb = tuple(q(v) for v in a), tuple(q(v) for v in b)
            ok = not any(closed_contact(qa, qb, c, d) for c, d in frozen_segments)
        cache[key] = ok
        return ok

    return ix, iy, allowed


def path_resources(points, xs, ys):
    """Expand compact segments back onto every critical-grid vertex/edge."""
    x_index = {x: i for i, x in enumerate(xs)}
    y_index = {y: i for i, y in enumerate(ys)}
    vertices = set()
    edges = set()
    for a, b in zip(points, points[1:]):
        if a[0] == b[0] and a[0] in x_index and a[1] in y_index and b[1] in y_index:
            lo, hi = sorted((y_index[a[1]], y_index[b[1]]))
            seq = [(a[0], ys[i]) for i in range(lo, hi + 1)]
        elif a[1] == b[1] and a[1] in y_index and a[0] in x_index and b[0] in x_index:
            lo, hi = sorted((x_index[a[0]], x_index[b[0]]))
            seq = [(xs[i], a[1]) for i in range(lo, hi + 1)]
        else:
            # Exact diagram endpoints are deliberately outside the graph.  The
            # adjacent legal stub is represented by the neighbouring segment.
            continue
        vertices.update(seq)
        edges.update(tuple(sorted((u, v))) for u, v in zip(seq, seq[1:]))
    return vertices, edges


def astar(route, nodes, xs, ys, ix, iy, allowed, vertex_use, edge_use,
          vertex_history, edge_history, present, bend_cost, rng, hard=False, noise=1e-7):
    start, start_stub, goal_stub, goal, sd, td = terminal_scaffold(route, nodes)
    if start_stub[0] not in ix or start_stub[1] not in iy or goal_stub[0] not in ix or goal_stub[1] not in iy:
        return None
    dirs = ((1, 0), (-1, 0), (0, 1), (0, -1))
    didx = {d: i for i, d in enumerate(dirs)}
    begin = (ix[start_stub[0]], iy[start_stub[1]], didx[sd])
    # Final graph edge must head opposite the target outward direction.
    final_dir = (-td[0], -td[1])
    goal_index = (ix[goal_stub[0]], iy[goal_stub[1]])
    pq = [(0.0, 0, begin)]
    dist = {begin: 0.0}
    parent = {begin: None}
    serial = itertools.count(1)

    def point(st):
        return (xs[st[0]], ys[st[1]])

    def heuristic(p):
        return abs(p[0] - goal_stub[0]) + abs(p[1] - goal_stub[1])

    while pq:
        _, _, state = heapq.heappop(pq)
        p = point(state)
        g = dist[state]
        if (state[0], state[1]) == goal_index and dirs[state[2]] == final_dir:
            raw = []
            cur = state
            while cur is not None:
                raw.append(point(cur)); cur = parent[cur]
            raw.reverse()
            # Keep every graph vertex, including the 0.10-cm source/target
            # stubs, while the route participates in negotiated occupancy.
            # Compacting here can erase a collinear stub; callers then omit
            # the endpoint segment from path_resources and allow undetected
            # contacts along the first/last long leg.  Output writers and
            # candidate-pool generators compact only after resource checks.
            return [start, *raw, goal]
        order = list(enumerate(dirs))
        rng.shuffle(order)
        for nd, (dx, dy) in order:
            ni, nj = state[0] + dx, state[1] + dy
            if not (0 <= ni < len(xs) and 0 <= nj < len(ys)):
                continue
            np = (xs[ni], ys[nj])
            if not allowed(p, np):
                continue
            edge = tuple(sorted((p, np)))
            if hard and (vertex_use[np] or edge_use[edge]):
                continue
            length = abs(np[0] - p[0]) + abs(np[1] - p[1])
            congestion = present * (vertex_use[np] + edge_use[edge])
            history = vertex_history[np] + edge_history[edge]
            turn = bend_cost if nd != state[2] else 0.0
            ng = g + length + turn + congestion + history + rng.random() * noise
            ns = (ni, nj, nd)
            if ng + 1e-10 < dist.get(ns, 1e100):
                dist[ns] = ng; parent[ns] = state
                heapq.heappush(pq, (ng + heuristic(np), next(serial), ns))
    return None


def conflicts(paths, xs, ys):
    vertex_owners = {}
    edge_owners = {}
    for rid, points in paths.items():
        verts, edges = path_resources(points[1:-1], xs, ys)
        for v in verts: vertex_owners.setdefault(v, []).append(rid)
        for e in edges: edge_owners.setdefault(e, []).append(rid)
    bad_v = {k: v for k, v in vertex_owners.items() if len(v) > 1}
    bad_e = {k: v for k, v in edge_owners.items() if len(v) > 1}
    return bad_v, bad_e


def exact_path_conflicts(paths):
    """Proof-grid independent final check for a complete tentative path set."""
    buckets = {}
    self_failures = []
    for rid, points in paths.items():
        try:
            buckets[rid] = [make_candidate({
                "routeId": rid, "family": "negotiated-final",
                "points": points, "cost": 0.0, "tag": rid,
            })]
        except CandidateError as exc:
            self_failures.append({"route": rid, "error": str(exc)})
    if self_failures:
        return {"selfFailures": self_failures, "crossRoutePairs": []}
    conflicts = build_conflicts(buckets)
    pairs = set()
    for rid, values in buckets.items():
        key = values[0].key
        for other_key in conflicts.get(key, set()):
            other = other_key.split(":", 1)[0] if ":" in other_key else other_key
            pairs.add(tuple(sorted((rid, other))))
    return {
        "selfFailures": [],
        "crossRoutePairs": [list(pair) for pair in sorted(pairs)],
    }


def solve(plan_id, iterations, seed, bend_cost, fixed_routes=None, route_ids=None,
          staging_out=STAGING, json_out=TRACE):
    sem, original, nodes, routes, overrides, frozen, mutable = load(plan_id)
    if fixed_routes:
        document = yaml.safe_load(Path(fixed_routes).read_text(encoding="utf-8")) or {}
        fixed_ids = set()
        for supplied in document.get("routes", []):
            rid = supplied["id"]
            if rid not in routes:
                continue
            merged = copy.deepcopy(routes[rid])
            merged.update({key: copy.deepcopy(value) for key, value in supplied.items() if key != "id"})
            frozen[f"seed:{rid}"] = route_points(merged, nodes)
            fixed_ids.add(rid)
        mutable = [route for route in mutable if route["id"] not in fixed_ids]
    if route_ids:
        wanted = set(route_ids)
        mutable = [route for route in mutable if route["id"] in wanted]
    xs, ys = build_axes(sem, mutable, nodes, frozen)
    ix, iy, allowed = build_graph(xs, ys, nodes, frozen)
    rng = random.Random(seed)
    vertex_history, edge_history = Counter(), Counter()
    paths = {}
    trace = []
    best_paths = {}
    best_score = (10**9, 10**9)
    best_conflicts = ({}, {})
    ids = [r["id"] for r in mutable]
    difficult = [rid for rid in [
        "A-M-UC-08", "A-CE-09", "A-PA-07", "A-B-06",
        "A-CD-UC-10", "A-M-UC-10", "A-T-UC-10", "A-T-UC-11",
    ] if rid in ids]
    by_id = {r["id"]: r for r in mutable}

    for iteration in range(iterations):
        vertex_use, edge_use = Counter(), Counter()
        if paths:
            for old_path in paths.values():
                old_vertices, old_edges = path_resources(old_path[1:-1], xs, ys)
                vertex_use.update(old_vertices); edge_use.update(old_edges)
        if iteration == 0:
            order = difficult + [rid for rid in ids if rid not in difficult]
        else:
            order = ids[:]
            rng.shuffle(order)
        new_paths = {}
        failed = []
        present = 1.0 + min(1000.0, iteration * 8.0)
        for rid in order:
            old_path = paths.get(rid)
            if old_path is not None:
                old_vertices, old_edges = path_resources(old_path[1:-1], xs, ys)
                vertex_use.subtract(old_vertices); edge_use.subtract(old_edges)
            path = astar(
                by_id[rid], nodes, xs, ys, ix, iy, allowed,
                vertex_use, edge_use, vertex_history, edge_history,
                present, bend_cost, rng,
            )
            if path is None:
                # Restore the previous legal path when this rip-up attempt
                # cannot find a replacement on the current projection.
                if old_path is not None:
                    path = old_path
                else:
                    failed.append(rid); continue
            new_paths[rid] = path
            verts, edges = path_resources(path[1:-1], xs, ys)
            vertex_use.update(verts); edge_use.update(edges)
        paths = new_paths
        bad_v, bad_e = conflicts(paths, xs, ys)
        score = (len(bad_v) + len(bad_e), len(bad_e))
        if not failed and score < best_score:
            best_score = score
            best_paths = copy.deepcopy(paths)
            best_conflicts = (copy.deepcopy(bad_v), copy.deepcopy(bad_e))
        for v, owners in bad_v.items(): vertex_history[v] += 20.0 * (len(owners) - 1)
        for e, owners in bad_e.items(): edge_history[e] += 30.0 * (len(owners) - 1)
        exact = None
        if not failed and not bad_v and not bad_e and len(paths) == len(mutable):
            exact = exact_path_conflicts(paths)
        record = {
            "iteration": iteration,
            "routed": len(paths),
            "failed": failed,
            "conflictingVertices": len(bad_v),
            "conflictingEdges": len(bad_e),
            "presentFactor": present,
        }
        if exact is not None:
            record["exactSelfFailureCount"] = len(exact["selfFailures"])
            record["exactCrossRoutePairCount"] = len(exact["crossRoutePairs"])
        trace.append(record)
        if iteration == 0 or iteration % 10 == 0 or (not failed and not bad_v and not bad_e):
            print(json.dumps(record, ensure_ascii=False), flush=True)
        if (
            not failed and not bad_v and not bad_e and len(paths) == len(mutable)
            and exact is not None
            and not exact["selfFailures"]
            and not exact["crossRoutePairs"]
        ):
            staged = copy.deepcopy(original)
            staged["metadata"]["status"] = "STAGING_GEOMETRY_CANDIDATE"
            for route in staged["routes"]:
                rid = route["id"]
                if rid not in paths:
                    continue
                route.update(overrides.get(rid, {}))
                route["waypoints"] = [[round(x, 2), round(y, 2)] for x, y in compact(paths[rid])[1:-1]]
                route["planningStatus"] = "ROUTE_PLANNED_PENDING_EXTERNAL_FREEZE"
            OUT.mkdir(parents=True, exist_ok=True)
            staging_out.write_text(yaml.safe_dump(staged, sort_keys=False), encoding="utf-8")
            payload = {
                "status": "PASS", "plan": plan_id, "seed": seed,
                "topologyGateStatus": topology_gate(plan_id)["status"],
                "orientableGenus": topology_gate(plan_id)["orientableGenus"],
                "iteration": iteration, "axisCounts": {"x": len(xs), "y": len(ys)},
                "trace": trace[-100:], "stagingCandidate": str(staging_out),
                "authoritativeCandidateModified": False,
                "frozenExtendIds": sorted(FROZEN),
            }
            json_out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
            return payload
    payload = {
        "status": "FAIL", "plan": plan_id, "seed": seed,
        "topologyGateStatus": topology_gate(plan_id)["status"],
        "orientableGenus": topology_gate(plan_id)["orientableGenus"],
        "axisCounts": {"x": len(xs), "y": len(ys)}, "trace": trace[-100:],
        "bestScore": list(best_score),
        "bestConflictVertices": [
            {"point": list(point), "routes": owners}
            for point, owners in sorted(best_conflicts[0].items())
        ],
        "bestConflictEdges": [
            {"edge": [list(edge[0]), list(edge[1])], "routes": owners}
            for edge, owners in sorted(best_conflicts[1].items())
        ],
        "authoritativeCandidateModified": False, "frozenExtendIds": sorted(FROZEN),
    }
    OUT.mkdir(parents=True, exist_ok=True)
    if best_paths:
        # Preserve the closest joint witness for blocker-directed rip-up.
        # This remains staging-only and is never promoted by this solver.
        staged = copy.deepcopy(original)
        staged["metadata"]["status"] = "STAGING_CONFLICT_WITNESS"
        for route in staged["routes"]:
            rid = route["id"]
            if rid not in best_paths:
                continue
            route.update(overrides.get(rid, {}))
            route["waypoints"] = [
                [round(x, 2), round(y, 2)]
                for x, y in compact(best_paths[rid])[1:-1]
            ]
            route["planningStatus"] = "ROUTE_PLANNED_CONFLICT_WITNESS"
        staging_out.write_text(yaml.safe_dump(staged, sort_keys=False), encoding="utf-8")
        payload["bestStagingCandidate"] = str(staging_out)
    json_out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return payload


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--plan", default="PLAN_O_M10_RIGHT_ESCAPE_B06_RIGHT")
    ap.add_argument("--iterations", type=int, default=250)
    ap.add_argument("--seed", type=int, default=12648430)
    ap.add_argument("--bend-cost", type=float, default=0.35)
    ap.add_argument("--fixed-routes", type=Path)
    ap.add_argument("--route-id", action="append", dest="route_ids")
    ap.add_argument("--staging-out", type=Path, default=STAGING)
    ap.add_argument("--json-out", type=Path, default=TRACE)
    args = ap.parse_args()
    result = solve(
        args.plan, args.iterations, args.seed, args.bend_cost,
        args.fixed_routes, args.route_ids, args.staging_out, args.json_out,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
