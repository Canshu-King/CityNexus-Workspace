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
