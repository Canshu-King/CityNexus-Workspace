"""Exact conflict-aware candidate selector for CityNexus P1 routing.

This helper deliberately does *not* generate paths.  It solves the second half
of the problem: given several deterministic family candidates per Association,
choose one candidate per route without geometric contact.

Expected candidate shape::

    {
      "routeId": "A-M-UC-08",
      "family": "bottom_right",
      "points": [[29.9, 7.6], [27.1, 7.6], ...],
      "cost": 123.4
    }

All contact checks are performed on exact 0.005-cm integer coordinates via
``critical_grid_geometry``.  This is intended to sit after candidate-family
path generation and before the official V2/V3 validators.
"""
from __future__ import annotations

from dataclasses import dataclass
from math import inf
import hashlib
import time
from typing import Iterable, Mapping, Sequence

from critical_grid_geometry import DEFAULT_SCALE, closed_contact, q


@dataclass(frozen=True)
class Candidate:
    route_id: str
    family: str
    points: tuple[tuple[int, int], ...]
    cost: float
    tag: str = ""

    @property
    def key(self) -> str:
        if self.tag:
            return self.tag
        digest = hashlib.sha256(repr(self.points).encode("ascii")).hexdigest()[:16]
        return f"{self.route_id}:{self.family}:{digest}"


class CandidateError(ValueError):
    pass


def self_contact_pairs(points: Sequence[tuple[int, int]]) -> list[tuple[int, int]]:
    """Return non-adjacent segment pairs that contact within one polyline.

    Adjacent segments intentionally share their common bend/endpoint and are
    therefore ignored.  Any other closed contact is illegal for a P1 route:
    self-crossing, self-overlap, self-T-junction, or retracing all create an
    ambiguous presentation route even when cross-route contact is zero.
    """
    segs = list(zip(points, points[1:]))
    bad = []
    for i, (a, b) in enumerate(segs):
        for j in range(i + 2, len(segs)):
            c, d = segs[j]
            if closed_contact(a, b, c, d):
                bad.append((i, j))
    return bad


def candidate_self_contacts(c: Candidate) -> list[tuple[int, int]]:
    return self_contact_pairs(c.points)


def _quantize_points(points: Sequence[Sequence[float]], scale: int) -> tuple[tuple[int, int], ...]:
    if len(points) < 2:
        raise CandidateError("polyline must contain at least two points")
    out = tuple((q(p[0], scale), q(p[1], scale)) for p in points)
    if any(a == b for a, b in zip(out, out[1:])):
        raise CandidateError("polyline contains a zero-length segment")
    for a, b in zip(out, out[1:]):
        if a[0] != b[0] and a[1] != b[1]:
            raise CandidateError(f"non-orthogonal segment: {a}->{b}")
    return out


def make_candidate(raw: Mapping, *, scale: int = DEFAULT_SCALE) -> Candidate:
    rid = str(raw["routeId"])
    family = str(raw.get("family", "default"))
    points = _quantize_points(raw["points"], scale)
    cost = float(raw.get("cost", 0.0))
    if cost < 0:
        raise CandidateError("candidate cost must be non-negative")
    tag = str(raw.get("tag", ""))
    bad = self_contact_pairs(points)
    if bad:
        raise CandidateError(f"polyline self-contact between segment pairs: {bad[:8]}")
    return Candidate(rid, family, points, cost, tag)


def segments(c: Candidate):
    return zip(c.points, c.points[1:])


def candidates_contact(a: Candidate, b: Candidate) -> bool:
    """Return True for any closed-segment contact between two route candidates.

    For P1 Association routing, unrelated presentation routes are not allowed to
    touch at all, including T-junctions and shared intermediate endpoints, so a
    closed contact test is intentionally strict.
    """
    for s1, e1 in segments(a):
        for s2, e2 in segments(b):
            if closed_contact(s1, e1, s2, e2):
                return True
    return False


def candidate_contacts_fixed(c: Candidate, fixed_polylines: Iterable[Sequence[Sequence[float]]], *, scale: int = DEFAULT_SCALE) -> bool:
    """Exact contact test against frozen/anchor polylines."""
    for i, pts in enumerate(fixed_polylines):
        fixed = Candidate(f"__fixed_{i}", "fixed", _quantize_points(pts, scale), 0.0)
        if candidates_contact(c, fixed):
            return True
    return False


def build_conflicts(candidates_by_route: Mapping[str, Sequence[Candidate]]):
    """Precompute candidate incompatibilities across distinct routes.

    Returns a dict keyed by candidate key whose value is a set of conflicting
    candidate keys.  Candidate keys must be unique.
    """
    flat = []
    seen = set()
    for rid, cs in candidates_by_route.items():
        for c in cs:
            if c.route_id != rid:
                raise CandidateError(f"candidate route mismatch: bucket={rid}, candidate={c.route_id}")
            if c.key in seen:
                raise CandidateError(f"duplicate candidate key: {c.key}")
            seen.add(c.key)
            flat.append(c)
    conflicts = {c.key: set() for c in flat}
    for i, a in enumerate(flat):
        for b in flat[i + 1 :]:
            if a.route_id == b.route_id:
                continue
            if candidates_contact(a, b):
                conflicts[a.key].add(b.key)
                conflicts[b.key].add(a.key)
    return conflicts


def route_pair_compatibility(
    candidates_by_route: Mapping[str, Sequence[Candidate]],
    *,
    conflicts=None,
):
    """Summarize discrete candidate-pool compatibility route pair by route pair.

    A pair with ``compatiblePairs == 0`` is a proof that the *current pool*
    cannot yield a complete solution, even if the underlying continuous
    routing problem is feasible.  This is the right trigger for targeted
    family generation, not more CP-SAT time.
    """
    if conflicts is None:
        conflicts = build_conflicts(candidates_by_route)
    routes = list(candidates_by_route)
    rows = []
    for i, first in enumerate(routes):
        first_values = candidates_by_route[first]
        for second in routes[i + 1:]:
            second_values = candidates_by_route[second]
            second_keys = {c.key for c in second_values}
            total = len(first_values) * len(second_values)
            blocked = sum(
                len(conflicts.get(c.key, set()) & second_keys)
                for c in first_values
            )
            compatible = total - blocked
            rows.append({
                "routeA": first,
                "routeB": second,
                "candidatePairs": total,
                "conflictingPairs": blocked,
                "compatiblePairs": compatible,
                "compatibilityRatio": (compatible / total) if total else 0.0,
            })
    return rows


def arc_consistency_prune(
    candidates_by_route: Mapping[str, Sequence[Candidate]],
    *,
    conflicts=None,
):
    """Enforce AC-3 style pairwise support across the candidate CSP.

    A candidate is removed when some other route has no remaining compatible
    candidate for it.  If a route domain becomes empty, the current discrete
    pool is proven infeasible without running CP-SAT/backtracking.
    """
    if conflicts is None:
        conflicts = build_conflicts(candidates_by_route)
    domains = {r: list(values) for r, values in candidates_by_route.items()}
    removals = []
    changed = True
    rounds = 0
    while changed:
        changed = False; rounds += 1
        for route, values in list(domains.items()):
            kept = []
            for candidate in values:
                unsupported_by = []
                blocked = conflicts.get(candidate.key, set())
                for other_route, other_values in domains.items():
                    if other_route == route:
                        continue
                    if not any(other.key not in blocked for other in other_values):
                        unsupported_by.append(other_route)
                if unsupported_by:
                    removals.append({
                        "route": route,
                        "candidate": candidate.key,
                        "unsupportedBy": unsupported_by,
                    })
                    changed = True
                else:
                    kept.append(candidate)
            domains[route] = kept
            if not kept:
                return {
                    "status": "FAIL",
                    "rounds": rounds,
                    "domains": domains,
                    "emptyRoutes": [r for r, vals in domains.items() if not vals],
                    "removals": removals,
                }
    return {
        "status": "PASS",
        "rounds": rounds,
        "domains": domains,
        "emptyRoutes": [],
        "removals": removals,
    }


def find_first_solution(
    candidates_by_route: Mapping[str, Sequence[Candidate]],
    *,
    conflicts=None,
    time_limit_seconds: float = 30.0,
):
    """Find any complete contact-free selection with MRV + LCV.

    Unlike ``solve_candidates`` this is a feasibility probe, not a cost
    optimizer.  It stops at the first complete assignment and therefore gives
    the repaired candidate pool a cheap non-OR-Tools path to an 18/18 witness.
    """
    routes = tuple(candidates_by_route)
    empty = [r for r in routes if not candidates_by_route[r]]
    if empty:
        return {"status": "FAIL", "reason": "empty-route-domain", "emptyRoutes": empty, "selection": {}, "expandedStates": 0}
    if conflicts is None:
        conflicts = build_conflicts(candidates_by_route)
    domain = {r: tuple(sorted(candidates_by_route[r], key=lambda c: (c.cost, c.family, c.key))) for r in routes}
    deadline = time.monotonic() + max(0.001, float(time_limit_seconds))
    expanded = 0
    max_depth = 0
    dead_end_counts = {}

    def compatible(candidate, selected):
        blocked = conflicts.get(candidate.key, set())
        return not any(chosen.key in blocked for chosen in selected.values())

    def impact(candidate, selected, skip_route):
        blocked = conflicts.get(candidate.key, set())
        total = 0
        for route, values in domain.items():
            if route in selected or route == skip_route:
                continue
            total += sum(value.key in blocked for value in values)
        return total

    def recurse(selected):
        nonlocal expanded, max_depth
        if time.monotonic() >= deadline:
            raise TimeoutError
        expanded += 1
        max_depth = max(max_depth, len(selected))
        if len(selected) == len(routes):
            return dict(selected)

        best_route = None; best_options = None; best_tie = None
        for route in routes:
            if route in selected:
                continue
            options = [c for c in domain[route] if compatible(c, selected)]
            if not options:
                dead_end_counts[route] = dead_end_counts.get(route, 0) + 1
                return None
            tie = (
                len(options),
                -sum(len(conflicts.get(c.key, ())) for c in options),
                route,
            )
            if best_tie is None or tie < best_tie:
                best_tie = tie; best_route = route; best_options = options
        best_options.sort(key=lambda c: (impact(c, selected, best_route), c.cost, c.key))
        for candidate in best_options:
            selected[best_route] = candidate
            result = recurse(selected)
            if result is not None:
                return result
            del selected[best_route]
        return None

    timed_out = False
    try:
        selection = recurse({})
    except TimeoutError:
        selection = None; timed_out = True
    return {
        "status": "PASS" if selection is not None else "FAIL",
        "reason": "complete-selection" if selection is not None else ("timeout" if timed_out else "exhausted"),
        "selection": selection or {},
        "expandedStates": expanded,
        "maxDepth": max_depth,
        "deadEndCounts": dict(sorted(dead_end_counts.items(), key=lambda item: (-item[1], item[0]))),
    }


def solve_candidates(
    candidates_by_route: Mapping[str, Sequence[Candidate]],
    *,
    conflicts=None,
    max_solutions: int = 1,
):
    """Exact MRV + forward-checking CSP selection.

    The solver minimizes total candidate cost among the explored combinations.
    ``max_solutions`` controls how many best complete solutions are retained.

    Return payload includes diagnostics useful for Codex repeat signatures and
    blocker-focused family generation.
    """
    if max_solutions < 1:
        raise ValueError("max_solutions must be >= 1")
    routes = tuple(candidates_by_route)
    if any(not candidates_by_route[r] for r in routes):
        empty = [r for r in routes if not candidates_by_route[r]]
        return {"status": "FAIL", "solutions": [], "emptyRoutes": empty, "deadEnds": [], "expandedStates": 0}
    if conflicts is None:
        conflicts = build_conflicts(candidates_by_route)

    # Stable cheap-first order within a route makes results reproducible.
    domain = {r: tuple(sorted(candidates_by_route[r], key=lambda c: (c.cost, c.family, c.key))) for r in routes}
    solutions: list[tuple[float, dict[str, Candidate]]] = []
    expanded = 0
    dead_ends = []

    def current_cutoff():
        return solutions[-1][0] if len(solutions) >= max_solutions else inf

    def compatible(c: Candidate, selected: Mapping[str, Candidate]) -> bool:
        bad = conflicts.get(c.key, set())
        return not any(s.key in bad for s in selected.values())

    def recurse(selected: dict[str, Candidate], running_cost: float):
        nonlocal expanded
        expanded += 1
        if running_cost >= current_cutoff():
            return
        if len(selected) == len(routes):
            solutions.append((running_cost, dict(selected)))
            solutions.sort(key=lambda x: x[0])
            del solutions[max_solutions:]
            return

        # MRV over currently compatible candidates; blocker degree is tie-break.
        best_route = None
        best_options = None
        best_tie = None
        for r in routes:
            if r in selected:
                continue
            opts = [c for c in domain[r] if compatible(c, selected)]
            blocker_degree = sum(len(conflicts.get(c.key, ())) for c in opts)
            tie = (len(opts), -blocker_degree, r)
            if best_tie is None or tie < best_tie:
                best_tie = tie
                best_route = r
                best_options = opts
        assert best_route is not None and best_options is not None

        if not best_options:
            blocker_keys = sorted({
                s.key
                for s in selected.values()
                if any(s.key in conflicts.get(c.key, set()) for c in domain[best_route])
            })
            dead_ends.append({
                "failedRoute": best_route,
                "selectedRoutes": sorted(selected),
                "blockerCandidates": blocker_keys,
            })
            return

        for c in best_options:
            selected[best_route] = c
            recurse(selected, running_cost + c.cost)
            del selected[best_route]

    recurse({}, 0.0)
    result_solutions = []
    for total, picked in solutions:
        result_solutions.append({
            "totalCost": total,
            "selection": {
                rid: {"key": c.key, "family": c.family, "cost": c.cost}
                for rid, c in sorted(picked.items())
            },
        })
    return {
        "status": "PASS" if result_solutions else "FAIL",
        "solutions": result_solutions,
        "emptyRoutes": [],
        "deadEnds": dead_ends[-100:],
        "expandedStates": expanded,
    }
