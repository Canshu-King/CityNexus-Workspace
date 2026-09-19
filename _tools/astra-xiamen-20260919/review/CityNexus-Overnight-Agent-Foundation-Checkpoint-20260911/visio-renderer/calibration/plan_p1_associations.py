"""PLAN_O-first global Association route workbench.

This is deliberately a staging planner.  It never edits the authoritative
candidate.  Paths are generated on a critical-coordinate rectilinear graph,
checked against nodes and frozen Extends, then selected jointly with the exact
candidate-family CSP helper.
"""
from __future__ import annotations

import argparse
import copy
import functools
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

from critical_grid_geometry import DEFAULT_SCALE, closed_contact, q, unq  # noqa: E402
from route_candidate_selector import (  # noqa: E402
    Candidate,
    build_conflicts,
    candidate_contacts_fixed,
    make_candidate,
    solve_candidates,
)
from routing_geometry import node_box, route_points, segment_intersects_box_interior, side_port  # noqa: E402
from audit_p1_route_topology_v2 import require_planar_topology  # noqa: E402

SEMANTIC = ROOT / "visio-spec" / "pages" / "p1_uc_overview.yaml"
CANDIDATE = RENDERER / "phase1-routing-rc6-candidate.yaml"
PLAN_FILE = HERE / "P1_ROUTE_PORT_PLANS.yaml"
SEEDS_FILE = HERE / "P1_ROUTE_FAMILY_SEEDS.yaml"
OUT = HERE / "out"
FROZEN = {"EXT-07-06", "EXT-09-08", "EXT-10-09"}

FAMILY_NAMES = ("default", "top_outer", "bottom_outer", "inner_left", "outer_right", "mandatory_gate")
SOURCE_STUB = {"traveler": 5.6, "provider": 28.0}

# These are mutable routing groups, not a permanent routing order.  The
# negotiated search changes the order between trials and backtracks within a
# trial.  Keeping their members adjacent makes rip-up diagnostics meaningful.
SUPER_BATCHES = (
    ("A-M-UC-08", "A-CE-09", "A-PA-07", "A-B-06"),
    ("A-CD-UC-10", "A-M-UC-10", "A-T-UC-10", "A-T-UC-11"),
)


def compact(points):
    out = []
    for p in points:
        p = (float(p[0]), float(p[1]))
        if not out or p != out[-1]:
            out.append(p)
    changed = True
    while changed and len(out) > 2:
        changed = False
        keep = [out[0]]
        for i in range(1, len(out) - 1):
            a, b, c = keep[-1], out[i], out[i + 1]
            collinear = (abs(a[0] - b[0]) <= 1e-9 and abs(b[0] - c[0]) <= 1e-9) or (
                abs(a[1] - b[1]) <= 1e-9 and abs(b[1] - c[1]) <= 1e-9
            )
            between = all(min(a[k], c[k]) - 1e-9 <= b[k] <= max(a[k], c[k]) + 1e-9 for k in (0, 1))
            if collinear and between:
                changed = True
                continue
            keep.append(b)
        keep.append(out[-1])
        out = keep
    return out


def load_inputs(plan_id):
    require_planar_topology(
        semantic=SEMANTIC, candidate=CANDIDATE, plans=PLAN_FILE, plan=plan_id,
    )
    sem = yaml.safe_load(SEMANTIC.read_text(encoding="utf-8"))
    cand = yaml.safe_load(CANDIDATE.read_text(encoding="utf-8"))
    nodes = {s["id"]: s for s in sem["shapes"] if s["id"] != "BOUNDARY"}
    routes = {r["id"]: copy.deepcopy(r) for r in cand["routes"]}
    plans = yaml.safe_load(PLAN_FILE.read_text(encoding="utf-8"))["plans"]
    def resolved_overrides(current, seen=()):
        if current in seen:
            raise ValueError(f"cyclic port-plan inheritance: {' -> '.join((*seen, current))}")
        try:
            plan = plans[current]
        except KeyError as exc:
            raise ValueError(f"unknown port plan: {current}") from exc
        parent = plan.get("basePlan")
        out = resolved_overrides(parent, (*seen, current)) if parent else {}
        out.update(copy.deepcopy(plan.get("routes", {})))
        return out

    overrides = resolved_overrides(plan_id)
    for rid, ov in overrides.items():
        if rid in routes:
            routes[rid].update(ov)
    frozen_paths = {rid: route_points(routes[rid], nodes) for rid in FROZEN}
    return sem, cand, nodes, routes, overrides, frozen_paths


def port_endpoints(route, nodes):
    start = side_port(nodes[route["source"]], route["sourceSide"], route["sourcePortFraction"])
    end = side_port(nodes[route["target"]], route["targetSide"], route["targetPortFraction"])
    # Keep the exact legal port values (including 0.005/0.01 fractions) while
    # removing binary floating noise from dictionary/grid lookups.
    return (round(float(start[0]), 3), round(float(start[1]), 3)), (round(float(end[0]), 3), round(float(end[1]), 3))


def axes_for(sem, nodes, routes, frozen_paths):
    # Coarse lattice plus exact terminals/frozen coordinates and 0.10 offsets.
    xs = {round(i / 10.0, 2) for i in range(int(float(sem["pageWidth"]) * 10) + 1)}
    ys = {round(i / 10.0, 2) for i in range(int(float(sem["pageHeight"]) * 10) + 1)}
    critical_x, critical_y = set(), set()
    # Node edges are routing-critical too.  Omitting them makes a path finder
    # discover a legal clearance lane only by walking the entire 0.10-cm
    # lattice, and previously violated the critical-coordinate graph contract.
    for node in nodes.values():
        box = node_box(node)
        critical_x.update((round(box.left, 3), round(box.right, 3)))
        critical_y.update((round(box.top, 3), round(box.bottom, 3)))
    for rid, r in routes.items():
        s, t = port_endpoints(r, nodes)
        critical_x.update((round(s[0], 3), round(t[0], 3)))
        critical_y.update((round(s[1], 3), round(t[1], 3)))
    for pts in frozen_paths.values():
        for x, y in pts:
            critical_x.add(round(float(x), 3)); critical_y.add(round(float(y), 3))
    for v in critical_x:
        for d in (-0.10, 0.0, 0.10):
            if 0 <= v + d <= float(sem["pageWidth"]):
                xs.add(round(v + d, 3))
    for v in critical_y:
        for d in (-0.10, 0.0, 0.10):
            if 0 <= v + d <= float(sem["pageHeight"]):
                ys.add(round(v + d, 3))
    return sorted(xs), sorted(ys)


def event_axes_for(sem, nodes, routes, frozen_paths):
    """Return a sparse turn-event projection of the full 0.10-cm graph.

    ``axes_for`` remains the proof grid: it contains every 0.10-cm lattice
    coordinate plus exact terminals and obstacle boundaries.  Orthogonal
    shortest paths only need to turn at an obstacle/terminal clearance lane,
    so this projection connects those turn events with exact segment checks.
    It avoids spending the route budget expanding thousands of identical
    interior cells while retaining the full grid for geometry accounting.
    """
    width, height = float(sem["pageWidth"]), float(sem["pageHeight"])
    raw_x = {0.0, width}
    raw_y = {0.0, height}
    for node in nodes.values():
        box = node_box(node)
        raw_x.update((box.left, box.right))
        raw_y.update((box.top, box.bottom))
    for fixed in frozen_paths.values():
        for x, y in fixed:
            raw_x.add(float(x)); raw_y.add(float(y))
    for route in routes.values():
        start, end = port_endpoints(route, nodes)
        raw_x.update((start[0], end[0]))
        raw_y.update((start[1], end[1]))
        if route["family"] in SOURCE_STUB:
            raw_x.add(SOURCE_STUB[route["family"]])
        gate = family_gate(route, "mandatory_gate")
        if gate:
            raw_x.update(gate[:2]); raw_y.update(gate[2:])
    # Broad outer lanes and several interior lanes keep the event graph
    # capable of generating independent corridor families, while every
    # obstacle/port receives an exact ±0.10 clearance option below.
    raw_x.update(float(v) for v in range(1, int(width)))
    raw_y.update(float(v) for v in range(1, int(height)))

    def coordset(values, limit):
        out = {0.0, round(limit, 3)}
        for value in values:
            for delta in (-0.10, 0.0, 0.10):
                point = value + delta
                if 0.0 <= point <= limit:
                    # Internal waypoints must be V3-normalizable.  Endpoints
                    # are restored below at their exact logical coordinates.
                    out.add(round(point, 2))
        return out

    xs = coordset(raw_x, width)
    ys = coordset(raw_y, height)
    for route in routes.values():
        start, end = port_endpoints(route, nodes)
        xs.update((start[0], end[0]))
        if route["family"] in SOURCE_STUB:
            xs.add(SOURCE_STUB[route["family"]])
        ys.update((start[1], end[1]))
    return sorted(xs), sorted(ys)


def orientation_dir(a, b):
    dx, dy = b[0] - a[0], b[1] - a[1]
    if abs(dx) > abs(dy):
        return (1 if dx > 0 else -1, 0)
    return (0, 1 if dy > 0 else -1)


def family_gate(route, family):
    rid = route["id"]
    # These are broad mandatory homotopy gates, not micro-jogs.
    special = {
        "A-T-UC-10": ("rect", (19.9, 22.9, 9.4, 11.3)),
        "A-M-UC-10": ("rect", (23.3, 28.0, 14.3, 17.8)),
        "A-CD-UC-10": ("rect", (20.0, 28.0, 14.3, 17.8)),
        "A-M-UC-08": ("rect", (11.2, 18.0, 13.5, 17.8)),
        "A-CE-09": ("rect", (14.0, 19.5, 15.9, 18.5)),
        "A-B-06": ("rect", (19.0, 28.0, 6.0, 7.5)),
        "A-PA-07": ("rect", (20.0, 28.0, 7.6, 8.0)),
    }
    if family == "mandatory_gate" and rid in special:
        return special[rid][1]
    if family == "top_outer":
        return (0.0, 33.87, 0.0, 2.5)
    if family == "bottom_outer":
        return (0.0, 33.87, 16.5, 19.05)
    if family == "inner_left":
        return (5.7, 14.5, 0.0, 19.05)
    if family == "outer_right":
        return (27.0, 30.0, 0.0, 19.05)
    return None


def in_gate(p, gate):
    return gate is not None and gate[0] - 1e-9 <= p[0] <= gate[1] + 1e-9 and gate[2] - 1e-9 <= p[1] <= gate[3] + 1e-9


def route_candidates(route, nodes, frozen_paths, xs, ys, family, max_expanded, deadline):
    source = nodes[route["source"]]
    target = nodes[route["target"]]
    start, goal = port_endpoints(route, nodes)
    stub_x = SOURCE_STUB[route["family"]]
    stub = (stub_x, start[1])
    # Preserve this route's exact terminal coordinates, but remove unrelated
    # three-decimal ports from its turn lattice.  Keeping them as adjacent
    # graph vertices made an otherwise legal two-decimal segment impossible
    # to traverse: the search would have to stop on an invalid waypoint.
    def turn_coordinate(value, terminal_values):
        return any(abs(value - terminal) <= 1e-9 for terminal in terminal_values) or abs(value - round(value, 2)) <= 1e-8

    xs = [x for x in xs if turn_coordinate(x, (start[0], goal[0], stub[0]))]
    ys = [y for y in ys if turn_coordinate(y, (start[1], goal[1], stub[1]))]
    outward = {"LEFT": (-1, 0), "RIGHT": (1, 0), "TOP": (0, -1), "BOTTOM": (0, 1)}[route["sourceSide"]]
    inward = {"LEFT": (1, 0), "RIGHT": (-1, 0), "TOP": (0, 1), "BOTTOM": (0, -1)}[route["targetSide"]]
    if route["sourceSide"] == "RIGHT" and stub_x <= start[0]:
        return None, {"reason": "stub"}
    if route["sourceSide"] == "LEFT" and stub_x >= start[0]:
        return None, {"reason": "stub"}
    ix = {x: i for i, x in enumerate(xs)}
    iy = {y: i for i, y in enumerate(ys)}
    # The grid indexes are split by coordinate axis; checking the complete
    # (x, y) tuple against ix would reject every valid terminal.
    if stub[0] not in ix or stub[1] not in iy or goal[0] not in ix or goal[1] not in iy:
        return None, {"reason": "axis", "stub": stub, "goal": goal}
    gate = family_gate(route, family)
    gate_active = gate is not None
    gate_start = in_gate(stub, gate)
    # Cost biases produce deterministic alternatives within a family.
    bias_kind = family
    dirs = ((1, 0), (-1, 0), (0, 1), (0, -1))
    didx = {d: i for i, d in enumerate(dirs)}
    start_state = (ix[stub[0]], iy[stub[1]], didx[outward], 1 if gate_start else 0)
    pq = [(0.0, 0, start_state)]
    dist = {start_state: 0.0}
    parent = {start_state: None}
    serial = itertools.count(1)
    expanded = 0
    node_boxes = tuple(node_box(node) for node in nodes.values())
    # Normalize every temporary obstacle to a pair of 2D points.  Candidate
    # paths are stored as ``[(x, y), ...]`` while the quantized Candidate
    # object stores integer tuples; accepting both here prevents a malformed
    # nested value from reaching ``closed_contact`` as a bare integer.
    frozen_segments = []
    for fixed in frozen_paths.values():
        if not isinstance(fixed, (list, tuple)):
            continue
        for a, b in zip(fixed, fixed[1:]):
            if not (isinstance(a, (list, tuple)) and isinstance(b, (list, tuple)) and len(a) == 2 and len(b) == 2):
                continue
            frozen_segments.append(((q(a[0]), q(a[1])), (q(b[0]), q(b[1]))))
    frozen_segments = tuple(frozen_segments)

    def point(st):
        return (xs[st[0]], ys[st[1]])

    @functools.lru_cache(maxsize=None)
    def blocked_segment(a, b):
        # A* reaches one geometric segment in several direction/gate states.
        # Collision truth is independent of that state, so memoize the exact
        # node/frozen-Extend scan rather than repeatedly redoing it.
        if b < a:
            a, b = b, a
        # All node interiors except the two terminals are hard obstacles.
        for box in node_boxes:
            if segment_intersects_box_interior(a, b, box):
                return True
        qa, qb = (q(a[0]), q(a[1])), (q(b[0]), q(b[1]))
        for c, d in frozen_segments:
            if closed_contact(qa, qb, c, d):
                return True
        return False

    def edge_ok(a, b, is_goal=False):
        if a == b or blocked_segment(a, b):
            return False
        # Never turn vertically in a source fan-out band.
        if route["sourceSide"] == "RIGHT" and min(a[0], b[0]) <= 5.6 + 1e-9 and max(a[0], b[0]) >= 4.4 - 1e-9 and abs(a[1] - b[1]) > 1e-9:
            return False
        if route["sourceSide"] == "LEFT" and min(a[0], b[0]) <= 29.9 + 1e-9 and max(a[0], b[0]) >= 28.0 - 1e-9 and abs(a[1] - b[1]) > 1e-9:
            return False
        # Keep route on the page and away from the actor interior.
        return True

    def heuristic(p):
        return abs(p[0] - goal[0]) + abs(p[1] - goal[1])

    while pq:
        if time.monotonic() > deadline:
            return None, {"reason": "deadline", "expanded": expanded}
        _, _, st = heapq.heappop(pq)
        p = point(st)
        g = dist[st]
        expanded += 1
        if expanded > max_expanded:
            return None, {"reason": "max_expanded", "expanded": expanded}
        if p == goal and st[2] == didx[inward] and (not gate_active or st[3]):
            raw = []
            cur = st
            while cur is not None:
                raw.append(point(cur)); cur = parent[cur]
            raw.reverse()
            full = compact([start, *raw])
            # The stub is a planning point and must remain the first waypoint.
            full = compact([start, *full[1:]])
            if len(full) < 3:
                continue
            if any(abs(v - round(v, 2)) > 1e-8 for pnt in full[1:-1] for v in pnt):
                continue
            if any(math.hypot(b[0] - a[0], b[1] - a[1]) < 0.099999 for a, b in zip(full, full[1:])):
                continue
            if any(blocked_segment(a, b) for a, b in zip(full, full[1:])):
                continue
            # A visited gate must survive normalization.  Reject loops and
            # retraced segments instead of erasing their mandatory excursion.
            if gate_active and not any(in_gate(pnt, gate) for pnt in full):
                continue
            segs = list(zip(full, full[1:]))
            if any(closed_contact(tuple(q(v) for v in a), tuple(q(v) for v in b),
                                  tuple(q(v) for v in c), tuple(q(v) for v in d))
                   for i, (a, b) in enumerate(segs)
                   for c, d in segs[i + 2:]):
                continue
            return full, {"reason": "ok", "expanded": expanded, "gate": gate}
        for d in dirs:
            nx, ny = p[0] + d[0] * 0, p[1] + d[1] * 0
            ni, nj = st[0] + d[0], st[1] + d[1]
            if ni < 0 or ni >= len(xs) or nj < 0 or nj >= len(ys):
                continue
            np = (xs[ni], ys[nj])
            if not edge_ok(p, np, np == goal):
                continue
            # Do not backtrack across the source actor boundary.
            if route["sourceSide"] == "RIGHT" and np[0] < 5.6 - 1e-9:
                continue
            if route["sourceSide"] == "LEFT" and np[0] > 28.0 + 1e-9:
                continue
            passed = st[3] or in_gate(np, gate)
            nd = didx[d]
            bend = 2.5 if nd != st[2] else 0.0
            penalty = 0.0
            if bias_kind == "top_outer": penalty += max(0.0, np[1] - 2.5) * 0.12
            elif bias_kind == "bottom_outer": penalty += max(0.0, 16.5 - np[1]) * 0.12
            elif bias_kind == "inner_left": penalty += max(0.0, np[0] - 14.5) * 0.10
            elif bias_kind == "outer_right": penalty += max(0.0, 27.0 - np[0]) * 0.10
            elif bias_kind == "mandatory_gate" and gate and not st[3]: penalty += 0.05
            ng = g + abs(np[0] - p[0]) + abs(np[1] - p[1]) + bend + penalty
            ns = (ni, nj, nd, int(bool(passed)))
            if ng + 1e-9 < dist.get(ns, 1e99):
                dist[ns] = ng
                parent[ns] = st
                heapq.heappush(pq, (ng + heuristic(np), next(serial), ns))
    return None, {"reason": "exhausted", "expanded": expanded}


def build_route_families(route, nodes, frozen_paths, xs, ys, args, deadline):
    out = []
    diagnostics = []
    for family in FAMILY_NAMES:
        # Give each homotopy family its own bounded slice.  Sharing one
        # per-route deadline across six families starved every family after
        # the first search and made diagnostics look like false empties.
        family_deadline = min(deadline, time.monotonic() + args.per_family_seconds)
        path, diag = route_candidates(route, nodes, frozen_paths, xs, ys, family, args.max_expanded, family_deadline)
        diagnostics.append({"family": family, **diag})
        if path is None:
            continue
        # Add a deterministic lane perturbation by temporarily using the same
        # solver with the next family; duplicate geometry is dropped later.
        raw = {"routeId": route["id"], "family": family, "points": [[x, y] for x, y in path], "cost": len(path) + diag.get("expanded", 0) / 100000.0}
        try:
            c = make_candidate(raw)
        except Exception:
            continue
        if any(candidate_contacts_fixed(c, frozen_paths.values()) for _ in [0]):
            continue
        out.append(c)
    unique = {}
    for c in out:
        unique.setdefault(c.points, c)
    return list(unique.values()), diagnostics


def negotiated_options(route, nodes, blocked_paths, xs, ys, args, deadline, family_offset=0):
    """Generate disjoint-safe alternatives against the current mutable batch.

    Unlike the static family workbench above, every call sees routes selected
    earlier in the current branch as hard temporary obstacles.  Consequently
    a route can take a longer legal corridor after a conflicting route has
    been provisionally selected, which is precisely the case a shortest-path
    candidate CSP cannot express.
    """
    options = []
    diagnostics = []
    families = FAMILY_NAMES[family_offset:] + FAMILY_NAMES[:family_offset]
    for family in families:
        if time.monotonic() >= deadline:
            break
        path, diag = route_candidates(
            route,
            nodes,
            blocked_paths,
            xs,
            ys,
            family,
            args.max_expanded,
            min(deadline, time.monotonic() + args.per_family_seconds),
        )
        diagnostics.append({"family": family, **diag})
        if path is None:
            continue
        try:
            candidate = make_candidate({
                "routeId": route["id"],
                "family": family,
                "points": [[x, y] for x, y in path],
                "cost": len(path) + diag.get("expanded", 0) / 100000.0,
            })
        except Exception as exc:
            diagnostics[-1]["candidateError"] = str(exc)
            continue
        # The route finder already considers blocked_paths, including the
        # frozen Extends.  Retain this independent exact check as a guard
        # against future path-finder changes.
        if candidate_contacts_fixed(candidate, blocked_paths.values()):
            diagnostics[-1]["candidateError"] = "contacted mutable/frozen obstacle"
            continue
        options.append(candidate)

    # Family gates may converge on the same geometry.  Candidate keys include
    # the family, but the negotiated DFS should not branch on duplicate paths.
    unique = {}
    for candidate in options:
        unique.setdefault(candidate.points, candidate)
    return list(unique.values()), diagnostics


def trial_route_order(associations, trial):
    """Return a deterministic, batch-aware rip-up order for one trial."""
    by_id = {route["id"]: route["id"] for route in associations}
    # First trial starts with the coupled routes whose shortest paths create
    # the known Booking/M10/Payment deadlock.  Later trials perturb the order
    # inside each mutable super-batch while retaining the face-scaffold groups.
    core = [rid for batch in SUPER_BATCHES for rid in batch if rid in by_id]
    remainder = [rid for rid in by_id if rid not in core]
    rng = random.Random(0xC17E + trial)
    if trial:
        rng.shuffle(core)
        rng.shuffle(remainder)
    else:
        core = [
            rid for rid in (
                "A-PA-07", "A-B-06", "A-M-UC-10", "A-CD-UC-10",
                "A-CE-09", "A-M-UC-08", "A-T-UC-10", "A-T-UC-11",
            ) if rid in by_id
        ]
        remainder = [
            rid for rid in (
                "A-M-UC-04", "A-CD-UC-04", "A-CD-UC-05",
                "A-T-UC-12", "A-T-UC-08", "A-T-UC-07", "A-T-UC-06",
                "A-T-UC-05", "A-T-UC-04", "A-T-UC-02",
            ) if rid in by_id and rid not in core
        ]
    return core + remainder


def solve_negotiated(associations, nodes, frozen_paths, xs, ys, args, deadline):
    """Bounded rip-up/backtracking router for the complete Association set.

    It deliberately treats every selected Association as provisional: when a
    later route has no legal corridor, the DFS removes the conflicting suffix
    and tries another family/corridor.  This is not a greedy sequential A*
    freeze.  The search is deterministic for a given trial count and records
    repeat signatures to expose cycle-like dead ends instead of hiding them.
    """
    by_id = {route["id"]: route for route in associations}
    state_budget = max(1, args.negotiated_state_budget)
    all_dead_ends = []
    cycles = []
    total_expanded = 0

    for trial in range(args.trials):
        if time.monotonic() >= deadline:
            break
        order = trial_route_order(associations, trial)
        selected = {}
        picks = []
        repeat_signatures = {}
        trial_states = 0

        def dfs(index):
            nonlocal trial_states, total_expanded
            if time.monotonic() >= deadline or total_expanded >= state_budget:
                return None
            if index == len(order):
                return dict(selected)
            rid = order[index]
            route = by_id[rid]
            option_deadline = min(
                deadline,
                # Each route may inspect every corridor family.  A
                # per-route slice shorter than six family slices starves the
                # later alternatives and falsely reports a hard dead-end.
                time.monotonic()
                + max(args.per_route_seconds, args.per_family_seconds * len(FAMILY_NAMES)),
            )
            options, option_diag = negotiated_options(
                route,
                nodes,
                {**frozen_paths, **selected},
                xs,
                ys,
                args,
                option_deadline,
                (trial + index) % len(FAMILY_NAMES),
            )
            trial_states += 1
            total_expanded += 1
            if not options:
                blocker_ids = tuple(sorted(selected))
                signature = (rid, blocker_ids)
                repeat_signatures[signature] = repeat_signatures.get(signature, 0) + 1
                detail = {
                    "trial": trial,
                    "failedRoute": rid,
                    "selectedRoutes": list(blocker_ids),
                    "familyDiagnostics": option_diag,
                    "state": trial_states,
                }
                all_dead_ends.append(detail)
                if repeat_signatures[signature] >= 2:
                    cycles.append({
                        "trial": trial,
                        "failedRoute": rid,
                        "blockerSet": list(blocker_ids),
                        "repetitions": repeat_signatures[signature],
                        "action": "backtrack-and-switch-corridor-family",
                    })
                return None

            # Try the ordinary local corridor first, then move outward by
            # family/cost during backtracking.  The known PA/B/M10 deadlock
            # has a feasible branch only after B switches from its direct
            # path to inner_left; trying every longest outer detour first
            # starved that branch before the global deadline.
            options.sort(key=lambda c: (c.cost, c.family, c.key))
            for candidate in options:
                selected[rid] = [(unq(x), unq(y)) for x, y in candidate.points]
                picks.append({"route": rid, "family": candidate.family, "key": candidate.key})
                solved = dfs(index + 1)
                if solved is not None:
                    return solved
                picks.pop()
                del selected[rid]
            return None

        solution = dfs(0)
        if solution is not None:
            return {
                "status": "PASS",
                "paths": solution,
                "trial": trial,
                "order": order,
                "picks": list(picks),
                "expandedStates": total_expanded,
                "deadEnds": all_dead_ends[-100:],
                "cycleDiagnostics": cycles[-100:],
            }

    return {
        "status": "FAIL",
        "paths": {},
        "expandedStates": total_expanded,
        "deadEnds": all_dead_ends[-100:],
        "cycleDiagnostics": cycles[-100:],
    }


def candidate_to_route(route, c):
    pts = list(c.points)
    mids = []
    for x, y in pts[1:-1]:
        px, py = round(unq(x), 2), round(unq(y), 2)
        mids.append([px, py])
    return compact_route_dict(route, mids)


def compact_route_dict(route, mids):
    out = copy.deepcopy(route)
    cleaned = []
    for p in mids:
        if not cleaned or p != cleaned[-1]:
            cleaned.append(p)
    changed = True
    while changed and len(cleaned) > 2:
        changed = False
        nxt = [cleaned[0]]
        for i in range(1, len(cleaned) - 1):
            a, b, c = nxt[-1], cleaned[i], cleaned[i + 1]
            if (a[0] == b[0] == c[0]) or (a[1] == b[1] == c[1]):
                changed = True
                continue
            nxt.append(b)
        nxt.append(cleaned[-1])
        cleaned = nxt
    out["waypoints"] = cleaned
    out["planningStatus"] = "ROUTE_PLANNED_PENDING_EXTERNAL_FREEZE"
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--plan", default="PLAN_O_PRESERVE_LOCAL_GEOMETRY")
    ap.add_argument("--global-seconds", type=float, default=90.0)
    ap.add_argument("--per-route-seconds", type=float, default=4.0)
    ap.add_argument("--per-family-seconds", type=float, default=1.5)
    ap.add_argument("--max-expanded", type=int, default=90000)
    ap.add_argument("--max-solutions", type=int, default=3)
    ap.add_argument("--trials", type=int, default=1)
    ap.add_argument(
        "--negotiated-only",
        action="store_true",
        help="skip static family CSP and spend the budget on mutable rip-up search",
    )
    ap.add_argument(
        "--negotiated-state-budget",
        type=int,
        default=800,
        help="bounded DFS states for mutable super-batch rip-up/backtracking",
    )
    ap.add_argument("--event-search", action="store_true", help="expand the exact turn-event projection of the full critical grid")
    args = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    start_time = time.monotonic()
    sem, original, nodes, routes, overrides, frozen_paths = load_inputs(args.plan)
    full_xs, full_ys = axes_for(sem, nodes, routes, frozen_paths)
    xs, ys = event_axes_for(sem, nodes, routes, frozen_paths) if args.event_search else (full_xs, full_ys)
    associations = [routes[rid] for rid in routes if routes[rid]["connectorType"] == "association"]
    families = {}
    family_diag = {}
    if not args.negotiated_only:
        for r in associations:
            if time.monotonic() - start_time > args.global_seconds:
                break
            fam, diag = build_route_families(r, nodes, frozen_paths, xs, ys, args, min(start_time + args.global_seconds, time.monotonic() + args.per_route_seconds))
            families[r["id"]] = fam
            family_diag[r["id"]] = diag

    domains = {rid: cs for rid, cs in families.items() if cs}
    conflicts = build_conflicts(domains) if domains else {}
    solver = solve_candidates(domains, conflicts=conflicts, max_solutions=args.max_solutions) if len(domains) == len(associations) else {"status": "FAIL", "solutions": [], "emptyRoutes": sorted(set(r["id"] for r in associations) - set(domains)), "deadEnds": [], "expandedStates": 0}
    negotiated = None
    # A static CSP can prove a short candidate combination impossible, but it
    # cannot express a route that must become longer after a neighbour is
    # provisionally selected.  Fall through to a bounded rip-up search before
    # declaring the staging workbench incomplete.
    if solver.get("status") != "PASS" and (args.negotiated_only or len(families) == len(associations)):
        negotiated = solve_negotiated(
            associations,
            nodes,
            frozen_paths,
            xs,
            ys,
            args,
            min(start_time + args.global_seconds, time.monotonic() + args.global_seconds),
        )
    solved = solver.get("status") == "PASS" or (negotiated and negotiated.get("status") == "PASS")
    trace = {
        "status": "PASS" if solved else "SEARCH_INCOMPLETE",
        "plan": args.plan,
        "associationCount": len(associations),
        "familyCounts": {rid: len(cs) for rid, cs in families.items()},
        "emptyRoutes": solver.get("emptyRoutes", []),
        "expandedStates": solver.get("expandedStates", 0) + (negotiated or {}).get("expandedStates", 0),
        "deadEnds": (negotiated or solver).get("deadEnds", [])[-100:],
        "authoritativeCandidateModified": False,
        "frozenExtendIds": sorted(FROZEN),
        "criticalAxisCounts": {"x": len(full_xs), "y": len(full_ys)},
        "searchAxisCounts": {"x": len(xs), "y": len(ys)},
        "searchMode": "event-projection" if args.event_search else "full-critical-grid",
        "familyDiagnostics": family_diag,
        "cycleDiagnostics": (negotiated or {}).get("cycleDiagnostics", []),
        "solutions": solver.get("solutions", []),
        "negotiated": {
            key: value for key, value in (negotiated or {}).items()
            if key != "paths"
        },
    }
    (OUT / "P1-CANDIDATE-FAMILY-DIAGNOSTICS.json").write_text(json.dumps(trace, ensure_ascii=False, indent=2), encoding="utf-8")
    if solved:
        selected = solver["solutions"][0]["selection"] if solver.get("status") == "PASS" else None
        by_key = {c.key: c for cs in families.values() for c in cs}
        negotiated_candidates = {
            rid: make_candidate({
                "routeId": rid,
                "family": "negotiated",
                "points": [[x, y] for x, y in points],
                "cost": len(points),
            })
            for rid, points in (negotiated or {}).get("paths", {}).items()
        }
        staged = copy.deepcopy(original)
        staged["metadata"]["status"] = "STAGING_GEOMETRY_CANDIDATE"
        for route in staged["routes"]:
            if route["id"] in overrides:
                route.update(overrides[route["id"]])
            candidate = (
                by_key[selected[route["id"]]["key"]]
                if selected and route["id"] in selected
                else negotiated_candidates.get(route["id"])
            )
            if candidate is not None:
                replacement = candidate_to_route(route, candidate)
                route.clear()
                route.update(replacement)
        (OUT / "P1-STAGING-CANDIDATE.yaml").write_text(yaml.safe_dump(staged, sort_keys=False), encoding="utf-8")
        trace["stagingCandidate"] = str(OUT / "P1-STAGING-CANDIDATE.yaml")
        (OUT / "P1-CANDIDATE-FAMILY-DIAGNOSTICS.json").write_text(json.dumps(trace, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(trace, ensure_ascii=False, indent=2))
    return 0 if solved else 2


if __name__ == "__main__":
    raise SystemExit(main())
