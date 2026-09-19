"""Pure geometry helpers for deterministic CityNexus orthogonal routing.

This module intentionally has no Visio/COM dependency.  It validates the route
plan before Codex asks Visio to realize the same ports and waypoints.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Sequence

Point = tuple[float, float]


@dataclass(frozen=True)
class Box:
    left: float
    top: float
    right: float
    bottom: float

    def contains_strict(self, p: Point, eps: float = 1e-9) -> bool:
        x, y = p
        return self.left + eps < x < self.right - eps and self.top + eps < y < self.bottom - eps


def node_box(node: dict) -> Box:
    return Box(
        float(node["x"]) - float(node["width"]) / 2,
        float(node["y"]) - float(node["height"]) / 2,
        float(node["x"]) + float(node["width"]) / 2,
        float(node["y"]) + float(node["height"]) / 2,
    )


def side_port(node: dict, side: str, fraction: float = 0.5) -> Point:
    """Return a logical top-left-origin port on one node side."""
    if not 0.0 <= float(fraction) <= 1.0:
        raise ValueError("port fraction must be between 0 and 1")
    b = node_box(node)
    f = float(fraction)
    if side == "LEFT":
        return (b.left, b.top + (b.bottom - b.top) * f)
    if side == "RIGHT":
        return (b.right, b.top + (b.bottom - b.top) * f)
    if side == "TOP":
        return (b.left + (b.right - b.left) * f, b.top)
    if side == "BOTTOM":
        return (b.left + (b.right - b.left) * f, b.bottom)
    raise ValueError(f"invalid side: {side}")


def is_orthogonal(a: Point, b: Point, eps: float = 1e-9) -> bool:
    return abs(a[0] - b[0]) <= eps or abs(a[1] - b[1]) <= eps


def path_is_orthogonal(points: Sequence[Point]) -> bool:
    return len(points) >= 2 and all(is_orthogonal(a, b) for a, b in zip(points, points[1:]))


def segment_intersects_box_interior(a: Point, b: Point, box: Box, eps: float = 1e-9) -> bool:
    """True when an orthogonal segment traverses a box interior."""
    if not is_orthogonal(a, b, eps):
        raise ValueError("segment is not orthogonal")
    x1, y1 = a
    x2, y2 = b
    if abs(y1 - y2) <= eps:
        y = y1
        lo, hi = sorted((x1, x2))
        return box.top + eps < y < box.bottom - eps and max(lo, box.left) < min(hi, box.right) - eps
    x = x1
    lo, hi = sorted((y1, y2))
    return box.left + eps < x < box.right - eps and max(lo, box.top) < min(hi, box.bottom) - eps


def proper_crossing(a: Point, b: Point, c: Point, d: Point, eps: float = 1e-9) -> bool:
    """Count only an interior H/V crossing, not shared endpoints."""
    if a in (c, d) or b in (c, d):
        return False
    ab_h = abs(a[1] - b[1]) <= eps
    cd_h = abs(c[1] - d[1]) <= eps
    if ab_h == cd_h:
        return False
    if not ab_h:
        return proper_crossing(c, d, a, b, eps)
    hx = sorted((a[0], b[0]))
    vy = sorted((c[1], d[1]))
    x, y = c[0], a[1]
    return hx[0] + eps < x < hx[1] - eps and vy[0] + eps < y < vy[1] - eps


def collinear_overlap(a: Point, b: Point, c: Point, d: Point, eps: float = 1e-9) -> bool:
    if abs(a[1] - b[1]) <= eps and abs(c[1] - d[1]) <= eps and abs(a[1] - c[1]) <= eps:
        lo1, hi1 = sorted((a[0], b[0])); lo2, hi2 = sorted((c[0], d[0]))
        return max(lo1, lo2) < min(hi1, hi2) - eps
    if abs(a[0] - b[0]) <= eps and abs(c[0] - d[0]) <= eps and abs(a[0] - c[0]) <= eps:
        lo1, hi1 = sorted((a[1], b[1])); lo2, hi2 = sorted((c[1], d[1]))
        return max(lo1, lo2) < min(hi1, hi2) - eps
    return False


def route_points(route: dict, nodes: dict[str, dict]) -> list[Point]:
    src = nodes[route["source"]]
    dst = nodes[route["target"]]
    start = side_port(src, route["sourceSide"], route.get("sourcePortFraction", 0.5))
    end = side_port(dst, route["targetSide"], route.get("targetPortFraction", 0.5))
    middle = [tuple(map(float, p)) for p in route.get("waypoints", [])]
    pts = [start, *middle, end]
    compact = [pts[0]]
    for p in pts[1:]:
        if p != compact[-1]: compact.append(p)
    return compact


def count_crossings(paths: dict[str, Sequence[Point]]) -> list[tuple[str, str]]:
    ids = list(paths)
    out = []
    for i, a_id in enumerate(ids):
        for b_id in ids[i + 1:]:
            if any(
                proper_crossing(a, b, c, d)
                for a, b in zip(paths[a_id], paths[a_id][1:])
                for c, d in zip(paths[b_id], paths[b_id][1:])
            ):
                out.append((a_id, b_id))
    return out


def count_overlaps(paths: dict[str, Sequence[Point]]) -> list[tuple[str, str]]:
    ids = list(paths)
    out = []
    for i, a_id in enumerate(ids):
        for b_id in ids[i + 1:]:
            if any(
                collinear_overlap(a, b, c, d)
                for a, b in zip(paths[a_id], paths[a_id][1:])
                for c, d in zip(paths[b_id], paths[b_id][1:])
            ):
                out.append((a_id, b_id))
    return out
