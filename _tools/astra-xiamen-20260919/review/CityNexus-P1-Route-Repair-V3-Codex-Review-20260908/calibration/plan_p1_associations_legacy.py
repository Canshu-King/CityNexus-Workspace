"""Bounded experimental orthogonal router for CityNexus P1 Associations.

Purpose
-------
Explore 0.10 cm grid routes for the 18 Association connectors while treating
all three C4E1 Extend routes as immutable hard obstacles.  This script is a
planning workbench only.  It never overwrites the authoritative candidate.

It writes best-partial/staging artifacts under calibration/out and records
bounded search evidence so a failed search does not masquerade as completion.
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
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
RENDERER = HERE.parent
ROOT = RENDERER.parent
sys.path.insert(0, str(RENDERER))
sys.path.insert(0, str(HERE))

from routing_geometry import node_box, path_is_orthogonal, route_points  # noqa:E402
from audit_p1_route_contacts import classify_contact  # noqa:E402
from validate_p1_route_candidate import tangent_ok  # noqa:E402

SEMANTIC = ROOT / "visio-spec" / "pages" / "p1_uc_overview.yaml"
CANDIDATE = RENDERER / "phase1-routing-rc6-candidate.yaml"
OUT = HERE / "out"

STEP_CM = 0.10
SCALE = 10
W = 338  # 33.8 cm grid; page is 33.87 cm
H = 190  # 19.0 cm grid; page is 19.05 cm
DIRS = [(1, 0), (-1, 0), (0, 1), (0, -1)]
DIDX = {d: i for i, d in enumerate(DIRS)}

FROZEN_EXTEND_IDS = {"EXT-07-06", "EXT-09-08", "EXT-10-09"}


def _load():
    sem = yaml.safe_load(SEMANTIC.read_text(encoding="utf-8"))
    cand = yaml.safe_load(CANDIDATE.read_text(encoding="utf-8"))
    nodes = {s["id"]: s for s in sem["shapes"] if s["id"] != "BOUNDARY"}
    by = {r["id"]: r for r in cand["routes"]}
    associations = [r["id"] for r in cand["routes"] if r["connectorType"] == "association"]
    extends = [r for r in cand["routes"] if r["connectorType"] == "extend"]
    if {r["id"] for r in extends} != FROZEN_EXTEND_IDS:
        raise RuntimeError("Frozen Extend set does not match C4E1 contract")
    return sem, cand, nodes, by, associations, extends


def _raster_segment(a, b):
    """Grid points touched by one orthogonal cm-space segment."""
    out = set()
    x1, y1 = a
    x2, y2 = b
    if abs(y1 - y2) < 1e-8:
        yi = round(y1 * SCALE)
        if abs(yi / SCALE - y1) < 1e-8:
            lo = math.ceil(min(x1, x2) * SCALE - 1e-8)
            hi = math.floor(max(x1, x2) * SCALE + 1e-8)
            out.update((xi, yi) for xi in range(lo, hi + 1))
    elif abs(x1 - x2) < 1e-8:
        xi = round(x1 * SCALE)
        if abs(xi / SCALE - x1) < 1e-8:
            lo = math.ceil(min(y1, y2) * SCALE - 1e-8)
            hi = math.floor(max(y1, y2) * SCALE + 1e-8)
            out.update((xi, yi) for yi in range(lo, hi + 1))
    else:
        raise ValueError(f"non-orthogonal segment {a}->{b}")
    return out


def _raster_path(points):
    out = set()
    for a, b in zip(points, points[1:]):
        out |= _raster_segment(a, b)
    return out


def _side_ports(node, side, margin=0.15):
    b = node_box(node)
    out = []
    if side in ("LEFT", "RIGHT"):
        x = b.left if side == "LEFT" else b.right
        xi = round(x * SCALE)
        if abs(xi / SCALE - x) > 1e-8:
            return out
        lo = math.ceil((b.top + margin) * SCALE - 1e-8)
        hi = math.floor((b.bottom - margin) * SCALE + 1e-8)
        for yi in range(lo, hi + 1):
            y = yi / SCALE
            f = (y - b.top) / (b.bottom - b.top)
            out.append(((xi, yi), f))
    else:
        y = b.top if side == "TOP" else b.bottom
        lo = math.ceil((b.left + margin) * SCALE - 1e-8)
        hi = math.floor((b.right - margin) * SCALE + 1e-8)
        for xi in range(lo, hi + 1):
            x = xi / SCALE
            f = (x - b.left) / (b.right - b.left)
            out.append(((xi, y), f))
    return out


def _build_blocked(nodes):
    blocked = set()
    for xi in range(W + 1):
        x = xi / SCALE
        for yi in range(H + 1):
            y = yi / SCALE
            for n in nodes.values():
                b = node_box(n)
                if b.left + 1e-9 < x < b.right - 1e-9 and b.top + 1e-9 < y < b.bottom - 1e-9:
                    blocked.add((xi, yi))
                    break
    return blocked


def _source_starts(route, nodes, blocked, occupied):
    side = route["sourceSide"]
    vals = []
    # Deliberately reserve a horizontal fan-out band beside shared actors.
    if side == "LEFT":
        stub_x = 280  # x=28.0, safely left of provider actor boundary x=29.9
        for port, frac in _side_ports(nodes[route["source"]], side):
            pre = (stub_x, port[1])
            xs = range(min(port[0], pre[0]), max(port[0], pre[0]) + 1)
            if any((x, port[1]) in blocked or (x, port[1]) in occupied for x in xs):
                continue
            vals.append((pre, port, frac, DIDX[(-1, 0)]))
    elif side == "RIGHT":
        stub_x = 56  # x=5.6, safely right of Traveler boundary x=4.4
        for port, frac in _side_ports(nodes[route["source"]], side):
            pre = (stub_x, port[1])
            xs = range(min(port[0], pre[0]), max(port[0], pre[0]) + 1)
            if any((x, port[1]) in blocked or (x, port[1]) in occupied for x in xs):
                continue
            vals.append((pre, port, frac, DIDX[(1, 0)]))
    else:
        raise RuntimeError(f"unexpected Association source side: {side}")
    return vals


def _goal_candidates(route, nodes, blocked, occupied):
    current = route.get("targetSide", "RIGHT")
    sides = [current] + [s for s in ("LEFT", "RIGHT", "TOP", "BOTTOM") if s != current]
    vals = []
    for side in sides:
        for port, frac in _side_ports(nodes[route["target"]], side, margin=0.18):
            if side == "LEFT":
                pre = (port[0] - 1, port[1])
            elif side == "RIGHT":
                pre = (port[0] + 1, port[1])
            elif side == "TOP":
                pre = (port[0], math.floor((float(port[1]) - 0.1000001) * SCALE))
            else:
                pre = (port[0], math.ceil((float(port[1]) + 0.1000001) * SCALE))
            if not (0 <= pre[0] <= W and 0 <= pre[1] <= H):
                continue
            if pre in blocked or pre in occupied:
                continue
            if side in ("LEFT", "RIGHT") and port in occupied:
                continue
            vals.append((pre, port, side, frac))
    return vals


def _astar(route, nodes, blocked, occupied, *, max_expanded, deadline, bend_cost=5.0):
    starts = _source_starts(route, nodes, blocked, occupied)
    goals = _goal_candidates(route, nodes, blocked, occupied)
    if not starts or not goals:
        return None, {"reason": "ports", "starts": len(starts), "goals": len(goals), "expanded": 0}

    goalmap = {g[0]: g for g in goals}
    vbands = []
    hbands = []
    for side in ("LEFT", "RIGHT"):
        pts = [g[0] for g in goals if g[2] == side]
        if pts:
            xs = {p[0] for p in pts}
            vbands.append((next(iter(xs)), min(p[1] for p in pts), max(p[1] for p in pts)))
    for side in ("TOP", "BOTTOM"):
        pts = [g[0] for g in goals if g[2] == side]
        if pts:
            ys = {p[1] for p in pts}
            hbands.append((next(iter(ys)), min(p[0] for p in pts), max(p[0] for p in pts)))

    def heur(p):
        x, y = p
        best = 10**9
        for gx, ylo, yhi in vbands:
            dy = 0 if ylo <= y <= yhi else (ylo - y if y < ylo else y - yhi)
            best = min(best, abs(x - gx) + dy)
        for gy, xlo, xhi in hbands:
            dx = 0 if xlo <= x <= xhi else (xlo - x if x < xlo else x - xhi)
            best = min(best, abs(y - gy) + dx)
        return best

    pq = []
    dist = {}
    parent = {}
    origin = {}
    counter = itertools.count()
    for pre, port, frac, direction in starts:
        st = (pre[0], pre[1], direction)
        dist[st] = 0.0
        parent[st] = None
        origin[st] = (port, frac)
        heapq.heappush(pq, (heur(pre), next(counter), st))

    expanded = 0
    best = None
    while pq:
        if time.monotonic() > deadline:
            return None, {"reason": "deadline", "expanded": expanded, "starts": len(starts), "goals": len(goals)}
        _, _, st = heapq.heappop(pq)
        x, y, old_dir = st
        g = dist[st]
        expanded += 1
        if expanded > max_expanded:
            return None, {"reason": "max_expanded", "expanded": expanded, "starts": len(starts), "goals": len(goals)}
        if (x, y) in goalmap:
            best = st
            break

        for new_dir, (dx, dy) in enumerate(DIRS):
            nx, ny = x + dx, y + dy
            if nx < 0 or nx > W or ny < 0 or ny > H:
                continue
            # Do not let one route turn vertically inside the shared source fan-out bands.
            if dy != 0 and route["sourceSide"] == "LEFT" and x >= 280:
                continue
            if dy != 0 and route["sourceSide"] == "RIGHT" and x <= 56:
                continue
            p = (nx, ny)
            if p in blocked or p in occupied:
                continue
            ng = g + 1.0 + (bend_cost if new_dir != old_dir else 0.0)
            ns = (nx, ny, new_dir)
            if ng + 1e-9 < dist.get(ns, 1e99):
                dist[ns] = ng
                parent[ns] = st
                origin[ns] = origin[st]
                heapq.heappush(pq, (ng + heur(p), next(counter), ns))

    if best is None:
        return None, {"reason": "exhausted", "expanded": expanded, "starts": len(starts), "goals": len(goals)}

    states = []
    s = best
    while s is not None:
        states.append(s)
        s = parent[s]
    states.reverse()
    grid_cm = [(s[0] / SCALE, s[1] / SCALE) for s in states]
    sport, sfrac = origin[best]
    _, tport, tside, tfrac = goalmap[(best[0], best[1])]
    sport_cm = (sport[0] / SCALE, sport[1] / SCALE)
    if tside in ("TOP", "BOTTOM"):
        tport_cm = (tport[0] / SCALE, float(tport[1]))
    else:
        tport_cm = (tport[0] / SCALE, tport[1] / SCALE)

    full = [sport_cm] + grid_cm + [tport_cm]
    compact = []
    for p in full:
        if not compact or p != compact[-1]:
            compact.append(p)
    out = [compact[0]]
    for i in range(1, len(compact) - 1):
        a, b, c = out[-1], compact[i], compact[i + 1]
        if (abs(a[0] - b[0]) < 1e-9 and abs(b[0] - c[0]) < 1e-9) or (
            abs(a[1] - b[1]) < 1e-9 and abs(b[1] - c[1]) < 1e-9
        ):
            continue
        out.append(b)
    out.append(compact[-1])
    compact = out

    result = copy.deepcopy(route)
    result["sourcePortFraction"] = float(sfrac)
    result["targetSide"] = tside
    result["targetPortFraction"] = float(tfrac)
    result["waypoints"] = [[round(float(x), 2), round(float(y), 2)] for x, y in compact[1:-1]]

    points = route_points(result, nodes)
    if not path_is_orthogonal(points) or not tangent_ok(points, result["sourceSide"], result["targetSide"]):
        return None, {"reason": "post_geometry", "expanded": expanded}
    for a, b in zip(points, points[1:]):
        if math.dist(a, b) < 0.10 - 1e-8:
            return None, {"reason": "short_after_compress", "expanded": expanded}
    segments = list(zip(points, points[1:]))
    for i, (a, b) in enumerate(segments):
        for j in range(i + 2, len(segments)):
            c, d = segments[j]
            if classify_contact(a, b, c, d):
                return None, {"reason": "self_contact", "expanded": expanded}

    return result, {
        "reason": "ok",
        "expanded": expanded,
        "pointCount": len(points),
        "targetSide": tside,
        "sourcePortFraction": float(sfrac),
        "targetPortFraction": float(tfrac),
    }


def _attempt(order, by, nodes, blocked, frozen_occ, *, max_expanded, per_route_seconds, global_deadline):
    occupied = set(frozen_occ)
    solved = {}
    logs = []
    for index, rid in enumerate(order):
        now = time.monotonic()
        if now >= global_deadline:
            return solved, {"route": rid, "reason": "global_deadline", "index": index}, logs
        route_deadline = min(global_deadline, now + per_route_seconds)
        rr, info = _astar(by[rid], nodes, blocked, occupied, max_expanded=max_expanded, deadline=route_deadline)
        logs.append({"index": index, "route": rid, **info})
        if rr is None:
            return solved, {"route": rid, "index": index, **info}, logs
        solved[rid] = rr
        occupied |= _raster_path(route_points(rr, nodes))
    return solved, None, logs


def _write_candidate(base, solved, associations, path, status):
    out = copy.deepcopy(base)
    out.setdefault("metadata", {})["status"] = status
    solved_ids = set(solved)
    for route in out["routes"]:
        rid = route["id"]
        if rid in solved_ids:
            route.clear()
            route.update(copy.deepcopy(solved[rid]))
            route["planningStatus"] = "EXPERIMENTAL_ROUTED_NOT_FROZEN"
        elif rid in associations:
            route["planningStatus"] = "PLANNING_REQUIRED"
    path.write_text(yaml.safe_dump(out, sort_keys=False, allow_unicode=True), encoding="utf-8")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--trials", type=int, default=60)
    ap.add_argument("--seed", type=int, default=20260907)
    ap.add_argument("--max-expanded", type=int, default=180000)
    ap.add_argument("--per-route-seconds", type=float, default=4.0)
    ap.add_argument("--global-seconds", type=float, default=90.0)
    args = ap.parse_args()

    sem, cand, nodes, by, associations, extends = _load()
    blocked = _build_blocked(nodes)
    frozen_occ = set()
    for r in extends:
        frozen_occ |= _raster_path(route_points(r, nodes))

    preferred = [
        "A-M-UC-08", "A-B-06", "A-PA-07", "A-CE-09",
        "A-CD-UC-10", "A-M-UC-10", "A-M-UC-04",
        "A-T-UC-10", "A-T-UC-12", "A-T-UC-08", "A-T-UC-11",
        "A-T-UC-07", "A-T-UC-06", "A-T-UC-05", "A-T-UC-04", "A-T-UC-02",
        "A-CD-UC-04", "A-CD-UC-05",
    ]
    if set(preferred) != set(associations):
        preferred = associations[:]

    rng = random.Random(args.seed)
    orders = [preferred]
    for _ in range(max(0, args.trials - 1)):
        order = associations[:]
        rng.shuffle(order)
        orders.append(order)

    OUT.mkdir(parents=True, exist_ok=True)
    global_deadline = time.monotonic() + args.global_seconds
    trace = []
    best = {}
    best_order = None
    best_failure = None
    full = None

    for trial, order in enumerate(orders):
        if time.monotonic() >= global_deadline:
            break
        solved, failure, logs = _attempt(
            order, by, nodes, blocked, frozen_occ,
            max_expanded=args.max_expanded,
            per_route_seconds=args.per_route_seconds,
            global_deadline=global_deadline,
        )
        trace.append({
            "trial": trial,
            "order": order,
            "solvedCount": len(solved),
            "solvedIds": list(solved),
            "failure": failure,
            "routes": logs,
        })
        if len(solved) > len(best):
            best = copy.deepcopy(solved)
            best_order = order[:]
            best_failure = copy.deepcopy(failure)
        if len(solved) == len(associations):
            full = solved
            break

    report = {
        "status": "FULL_GEOMETRY_CANDIDATE_FOUND" if full else "SEARCH_INCOMPLETE",
        "gridCm": STEP_CM,
        "trialCountRequested": args.trials,
        "trialCountExecuted": len(trace),
        "bestSolvedCount": len(full or best),
        "associationCount": len(associations),
        "bestOrder": best_order,
        "bestFailure": best_failure,
        "frozenExtendIds": sorted(FROZEN_EXTEND_IDS),
        "authoritativeCandidateModified": False,
        "warning": "Do not render or promote RC6 from planner output. Copy to the official candidate only after external review, then run V2/V3 and the complete test suite.",
        "trace": trace,
    }
    (OUT / "P1-ASTAR-PLANNER-TRACE.json").write_text(json.dumps(report, indent=2), encoding="utf-8")

    chosen = full or best
    _write_candidate(
        cand,
        chosen,
        associations,
        OUT / ("P1-ASTAR-STAGING-CANDIDATE.yaml" if full else "P1-ASTAR-BEST-PARTIAL.yaml"),
        "EXPERIMENTAL_FULL_NOT_VALIDATED" if full else "EXPERIMENTAL_PARTIAL_DO_NOT_RENDER",
    )

    print(json.dumps({k: v for k, v in report.items() if k != "trace"}, indent=2))
    return 0 if full else 2


if __name__ == "__main__":
    raise SystemExit(main())
