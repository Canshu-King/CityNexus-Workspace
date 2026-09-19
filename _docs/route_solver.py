from __future__ import annotations

import heapq
import math
import random
from copy import deepcopy
from pathlib import Path

import yaml

ROOT = Path(r"D:/moodle/CityNexus")
RENDERER = ROOT / "visio-renderer"
SEMANTIC = ROOT / "visio-spec/pages/p1_uc_overview.yaml"
CANDIDATE = RENDERER / "phase1-routing-rc6-candidate.yaml"
OUT = ROOT / "route-solved.yaml"
SCALE = 2
W = 67
H = 38

sem = yaml.safe_load(SEMANTIC.read_text(encoding="utf-8"))
base = yaml.safe_load(CANDIDATE.read_text(encoding="utf-8"))
nodes = {s["id"]: s for s in sem["shapes"] if s["id"] != "BOUNDARY"}


def box(n):
    return (n["x"] - n["width"] / 2, n["y"] - n["height"] / 2,
            n["x"] + n["width"] / 2, n["y"] + n["height"] / 2)


def pgrid(p):
    return (round(float(p[0]) * SCALE), round(float(p[1]) * SCALE))


def pfloat(p):
    return (p[0] / SCALE, p[1] / SCALE)


def port(node, side, frac):
    l, t, r, b = box(node)
    f = float(frac)
    return {"LEFT": (l, t + (b - t) * f), "RIGHT": (r, t + (b - t) * f),
            "TOP": (l + (r - l) * f, t), "BOTTOM": (l + (r - l) * f, b)}[side]


def frac_for(node, side, point):
    l, t, r, b = box(node)
    if side in ("LEFT", "RIGHT"):
        return (point[1] - t) / (b - t)
    return (point[0] - l) / (r - l)


def inside(p, node):
    l, t, r, b = box(node)
    x, y = pfloat(p)
    return l * SCALE < x * SCALE < r * SCALE and t * SCALE < y * SCALE < b * SCALE


def segment_inside(a, b, node):
    x1, y1 = pfloat(a); x2, y2 = pfloat(b)
    l, t, r, bt = box(node)
    if y1 == y2:
        return t < y1 < bt and max(min(x1, x2), l) < min(max(x1, x2), r)
    return l < x1 < r and max(min(y1, y2), t) < min(max(y1, y2), bt)


def simplify(points):
    out = [points[0]]
    for p in points[1:]:
        if p == out[-1]:
            continue
        if len(out) >= 2:
            a, b = out[-2], out[-1]
            if (a[0] == b[0] == p[0]) or (a[1] == b[1] == p[1]):
                out[-1] = p
                continue
        out.append(p)
    return out


def route_points(route):
    return [pgrid(port(nodes[route["source"]], route["sourceSide"], route["sourcePortFraction"])),
            *[pgrid(p) for p in route.get("waypoints", [])],
            pgrid(port(nodes[route["target"]], route["targetSide"], route["targetPortFraction"]))]


def raster_path(points):
    cells = set()
    for a, b in zip(points, points[1:]):
        x, y = a; tx, ty = b
        dx = (tx > x) - (tx < x); dy = (ty > y) - (ty < y)
        while True:
            cells.add((x, y))
            if (x, y) == (tx, ty):
                break
            x += dx; y += dy
    return cells


def clean_path(points):
    return simplify(points)


def tangent(route, a, b, start):
    dx, dy = b[0] - a[0], b[1] - a[1]
    side = route["sourceSide"] if start else route["targetSide"]
    return ((side == "RIGHT" and dx > 0) or (side == "LEFT" and dx < 0) or
            (side == "TOP" and dy < 0) or (side == "BOTTOM" and dy > 0)) if start else (
            (side == "LEFT" and dx > 0) or (side == "RIGHT" and dx < 0) or
            (side == "TOP" and dy > 0) or (side == "BOTTOM" and dy < 0))


def astar(route, start, goal, occupied, seed):
    rng = random.Random(seed)
    blocked = set(BASE_BLOCKED)
    for node_id in (route["source"], route["target"]):
        blocked.difference_update(NODE_INTERIORS[node_id])
    # One-cell clearance keeps separate routes from sharing or touching.
    for x, y in occupied:
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                blocked.add((x + dx, y + dy))
    if start in occupied or goal in occupied:
        return None
    blocked.discard(start); blocked.discard(goal)
    q = [(0.0, 0, start, None)]
    dist = {(start, None): 0.0}
    prev = {}
    serial = 0
    while q:
        _, _, u, last = heapq.heappop(q)
        if u == goal:
            state = (u, last); out = []
            while state in prev:
                out.append(state[0]); state = prev[state]
            out.append(start); out.reverse()
            return clean_path(out)
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            v = (u[0] + dx, u[1] + dy)
            if not (0 <= v[0] <= W and 0 <= v[1] <= H) or v in blocked:
                continue
            if u == start and not tangent(route, u, v, True):
                continue
            if v == goal and not tangent(route, u, v, False):
                continue
            if any(segment_inside(u, v, n) for n in nodes.values()
                   if n["id"] not in (route["source"], route["target"])):
                continue
            direction = (dx, dy)
            bend = 2.0 if last is not None and direction != last else 0.0
            ng = dist[(u, last)] + 1.0 + bend + rng.random() * 0.01
            state = (v, direction)
            if ng < dist.get(state, 1e18):
                dist[state] = ng
                prev[state] = (u, last)
                serial += 1
                h = abs(v[0] - goal[0]) + abs(v[1] - goal[1])
                heapq.heappush(q, (ng + h, serial, v, direction))
    return None


def endpoint_candidates(route):
    source_node = nodes[route["source"]]
    target_node = nodes[route["target"]]
    source_side = route["sourceSide"]
    target_sides = [route["targetSide"]] + [s for s in ("LEFT", "RIGHT", "TOP", "BOTTOM") if s != route["targetSide"]]
    source_points = []
    l, t, r, b = box(source_node)
    if source_side in ("LEFT", "RIGHT"):
        for y in range(round(t * SCALE) + 1, round(b * SCALE)):
            source_points.append((round((r if source_side == "RIGHT" else l) * SCALE), y))
    else:
        for x in range(round(l * SCALE) + 1, round(r * SCALE)):
            source_points.append((x, round((b if source_side == "BOTTOM" else t) * SCALE)))
    goals = []
    l, t, r, b = box(target_node)
    for side in target_sides:
        if side in ("LEFT", "RIGHT"):
            x = round((l if side == "LEFT" else r) * SCALE)
            for y in range(round(t * SCALE) + 1, round(b * SCALE)):
                goals.append((side, (x, y)))
        else:
            y = round((t if side == "TOP" else b) * SCALE)
            for x in range(round(l * SCALE) + 1, round(r * SCALE)):
                goals.append((side, (x, y)))
    return source_points, goals


NODE_INTERIORS = {}
for node_id, node in nodes.items():
    NODE_INTERIORS[node_id] = {
        (x, y) for x in range(W + 1) for y in range(H + 1) if inside((x, y), node)
    }
BASE_BLOCKED = set().union(*NODE_INTERIORS.values())


def solve(order, attempts=40):
    frozen = {r["id"]: route_points(r) for r in base["routes"] if r.get("planningStatus") == "FROZEN_FROM_C4E1"}
    # The two zero-conflict provider routes are accepted obstacles for the repair.
    frozen.update({rid: route_points(r) for rid, r in ((x["id"], x) for x in base["routes"])
                   if rid in {"A-CD-UC-04", "A-CD-UC-05"}})
    associations = [r for r in base["routes"] if r.get("planningStatus") != "FROZEN_FROM_C4E1"]
    for attempt in range(attempts):
        rng = random.Random(1000 + attempt)
        paths = dict(frozen)
        remaining = list(associations)
        if order == "random":
            rng.shuffle(remaining)
            remaining.sort(key=lambda r: (r["id"] not in {"A-T-UC-04", "A-M-UC-08", "A-T-UC-05", "A-B-06"}))
        else:
            remaining.sort(key=lambda r: (r["family"] == "traveler", r["target"], r["source"]))
        success = True
        for route in remaining:
            sources, goals = endpoint_candidates(route)
            rng.shuffle(sources); rng.shuffle(goals)
            best = None
            occupied = set().union(*(raster_path(p) for p in paths.values()))
            for source in sources[:min(12, len(sources))]:
                for target_side, goal in goals[:min(60, len(goals))]:
                    route["targetSide"] = target_side
                    candidate = astar(route, source, goal, occupied, attempt * 10000 + source[1] + goal[0])
                    if candidate:
                        best = (candidate, target_side, source, goal)
                        break
                if best:
                    break
            if not best:
                success = False
                break
            candidate, target_side, source, goal = best
            paths[route["id"]] = candidate
            route["targetSide"] = target_side
            route["sourcePortFraction"] = frac_for(nodes[route["source"]], route["sourceSide"], pfloat(source))
            route["targetPortFraction"] = frac_for(nodes[route["target"]], target_side, pfloat(goal))
            route["waypoints"] = [[round(x / SCALE, 2), round(y / SCALE, 2)] for x, y in candidate[1:-1]]
            route["planningStatus"] = "ROUTE_PLANNED_PENDING_EXTERNAL_FREEZE"
        if success:
            out = deepcopy(base)
            by_id = {r["id"]: r for r in out["routes"]}
            for rid, path in paths.items():
                if by_id[rid].get("planningStatus") == "FROZEN_FROM_C4E1":
                    continue
                side = by_id[rid]["targetSide"]
                src = pfloat(path[0]); dst = pfloat(path[-1])
                by_id[rid]["sourcePortFraction"] = frac_for(nodes[by_id[rid]["source"]], by_id[rid]["sourceSide"], src)
                by_id[rid]["targetPortFraction"] = frac_for(nodes[by_id[rid]["target"]], side, dst)
                by_id[rid]["waypoints"] = [[round(x, 2), round(y, 2)] for x, y in map(pfloat, path[1:-1])]
                by_id[rid]["planningStatus"] = "ROUTE_PLANNED_PENDING_EXTERNAL_FREEZE"
            out["metadata"]["status"] = "GEOMETRY_PASS_PENDING_EXTERNAL_FREEZE"
            OUT.write_text(yaml.safe_dump(out, sort_keys=False, allow_unicode=True), encoding="utf-8")
            print("FOUND", attempt, len(paths))
            return 0
        print("attempt", attempt, "failed at", route["id"])
    return 1


if __name__ == "__main__":
    raise SystemExit(solve("random", 15))
