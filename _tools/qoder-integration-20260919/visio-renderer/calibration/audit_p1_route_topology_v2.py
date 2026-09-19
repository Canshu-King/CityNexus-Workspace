#!/usr/bin/env python3
"""Hardened, reusable topology pre-gate for CityNexus P1 routing.

The gate validates a port-plan override and computes the orientable genus of
its rotation system using route-id darts.  It is deliberately geometry-free:
a PASS means only that the chosen endpoint rotation admits a planar embedding.
V1/V2/V3 remain authoritative for actual orthogonal route geometry.

This module is both a CLI and an importable runtime guard.  Solvers should call
``require_planar_topology`` *before* spending time on path search.
"""
from __future__ import annotations

import argparse
import json
from collections import defaultdict, deque
from pathlib import Path
from typing import Any

import yaml

ALLOWED_OVERRIDE_KEYS = {"sourcePortFraction", "targetSide", "targetPortFraction"}
VALID_SIDES = {"LEFT", "RIGHT", "TOP", "BOTTOM"}
FROZEN_EXTEND_IDS = {"EXT-07-06", "EXT-09-08", "EXT-10-09"}


class TopologyGateError(ValueError):
    """Raised when a routing plan fails the topology pre-gate."""

    def __init__(self, payload: dict[str, Any]):
        self.payload = payload
        details = "; ".join(payload.get("failures") or ["topology gate failed"])
        super().__init__(f"P1 topology pre-gate FAIL for {payload.get('plan')}: {details}")


def node_box(n):
    x = float(n["x"]); y = float(n["y"]); w = float(n["width"]); h = float(n["height"])
    return x - w / 2, y - h / 2, x + w / 2, y + h / 2


def perimeter_cw(n, side, fraction):
    l, t, r, b = node_box(n); w = r - l; h = b - t; f = float(fraction)
    if side == "TOP": return f * w
    if side == "RIGHT": return w + f * h
    if side == "BOTTOM": return w + h + (1 - f) * w
    if side == "LEFT": return 2 * w + h + (1 - f) * h
    raise ValueError(f"bad side {side}")


def _resolved_plan(plans: dict[str, Any], plan_id: str, seen=()):
    if plan_id in seen:
        raise ValueError(f"cyclic port-plan inheritance: {' -> '.join((*seen, plan_id))}")
    if plan_id not in plans:
        raise ValueError(f"plan not found: {plan_id}; available={list(plans)}")
    plan = plans[plan_id] or {}
    parent = plan.get("basePlan")
    resolved = _resolved_plan(plans, parent, (*seen, plan_id)) if parent else {}
    routes = plan.get("routes", {}) or {}
    for rid, values in routes.items():
        merged = dict(resolved.get(rid, {}))
        merged.update(values or {})
        resolved[rid] = merged
    return resolved


def load_plan(path, plan_id, candidate_by_id):
    if not path or not plan_id:
        return {}, []
    doc = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
    plans = doc.get("plans", {})
    failures = []
    try:
        overrides = _resolved_plan(plans, plan_id)
    except ValueError as exc:
        return {}, [str(exc)]

    for rid, ov in overrides.items():
        if rid not in candidate_by_id:
            failures.append(f"plan override references unknown route:{rid}")
            continue
        base = candidate_by_id[rid]
        if base.get("connectorType") != "association":
            failures.append(f"plan override is not an Association:{rid}")
        bad = set(ov) - ALLOWED_OVERRIDE_KEYS
        if bad:
            failures.append(f"plan override changes prohibited fields:{rid}:{sorted(bad)}")
        if rid in FROZEN_EXTEND_IDS:
            failures.append(f"frozen Extend override prohibited:{rid}")
    return overrides, failures


def is_connected(vertices, edges):
    if not vertices:
        return True
    graph = defaultdict(list)
    for _, u, v in edges:
        graph[u].append(v); graph[v].append(u)
    start = next(iter(vertices)); seen = {start}; queue = deque([start])
    while queue:
        u = queue.popleft()
        for v in graph[u]:
            if v not in seen:
                seen.add(v); queue.append(v)
    return seen == set(vertices)


def audit_topology(*, semantic, candidate, plans=None, plan=None) -> dict[str, Any]:
    """Return a complete topology pre-gate payload without writing files."""
    semantic = Path(semantic); candidate = Path(candidate)
    sem = yaml.safe_load(semantic.read_text(encoding="utf-8"))
    cand = yaml.safe_load(candidate.read_text(encoding="utf-8"))
    nodes = {s["id"]: s for s in sem["shapes"] if s["id"] != "BOUNDARY"}
    candidate_by_id = {r["id"]: r for r in cand["routes"]}
    overrides, failures = load_plan(plans, plan, candidate_by_id)

    edges = []
    incidence = defaultdict(list)
    endpoint_port = {}
    endpoint_neighbour = {}

    for base in cand["routes"]:
        route = dict(base)
        if route["id"] in overrides:
            route.update(overrides[route["id"]])
        rid = route["id"]; u = route["source"]; v = route["target"]
        if u not in nodes or v not in nodes:
            failures.append(f"route references missing node:{rid}:{u}->{v}")
            continue
        for side_key in ("sourceSide", "targetSide"):
            if route.get(side_key) not in VALID_SIDES:
                failures.append(f"invalid side:{rid}:{side_key}={route.get(side_key)!r}")
        fractions = {}
        for frac_key in ("sourcePortFraction", "targetPortFraction"):
            try:
                value = float(route.get(frac_key))
            except Exception:
                failures.append(f"invalid fraction:{rid}:{frac_key}={route.get(frac_key)!r}")
                value = -1.0
            fractions[frac_key] = value
            if not 0.0 < value < 1.0:
                failures.append(f"fraction outside (0,1):{rid}:{frac_key}={value}")
        edges.append((rid, u, v))
        incidence[u].append((rid, 0)); incidence[v].append((rid, 1))
        endpoint_neighbour[(rid, 0)] = v; endpoint_neighbour[(rid, 1)] = u
        endpoint_port[(rid, 0)] = (route["sourceSide"], fractions["sourcePortFraction"])
        endpoint_port[(rid, 1)] = (route["targetSide"], fractions["targetPortFraction"])

    active = set(incidence)
    if not is_connected(active, edges):
        failures.append("connector graph is disconnected; this gate expects one connected embedding")

    sigma = {}
    rotation_routes = {}
    rotation_neighbours = {}
    port_detail = {}
    for node_id, darts in incidence.items():
        arr = []
        for dart in darts:
            rid, end = dart; side, frac = endpoint_port[dart]
            p = perimeter_cw(nodes[node_id], side, frac)
            arr.append((p, rid, end, endpoint_neighbour[dart], side, frac))
        arr.sort(key=lambda x: (x[0], x[1], x[2]))
        for first, second in zip(arr, arr[1:]):
            if abs(first[0] - second[0]) < 1e-9:
                failures.append(
                    f"{node_id}: duplicate perimeter port position for {first[1]} and {second[1]}"
                )
        rotation = [(rid, end) for _, rid, end, _, _, _ in arr]
        for i, dart in enumerate(rotation):
            sigma[dart] = rotation[(i + 1) % len(rotation)]
        rotation_routes[node_id] = [rid for _, rid, _, _, _, _ in arr]
        rotation_neighbours[node_id] = [nb for _, _, _, nb, _, _ in arr]
        port_detail[node_id] = [
            {"route": rid, "endpoint": end, "neighbor": nb, "side": side,
             "fraction": frac, "perimeterCW": p}
            for p, rid, end, nb, side, frac in arr
        ]

    alpha = {}
    for rid, _, _ in edges:
        alpha[(rid, 0)] = (rid, 1); alpha[(rid, 1)] = (rid, 0)
    phi = {dart: sigma[alpha[dart]] for dart in alpha if alpha[dart] in sigma}

    seen = set(); faces = []; dart_face = {}
    for dart in phi:
        if dart in seen:
            continue
        face_id = len(faces); cur = dart; seq = []
        while cur not in seen:
            seen.add(cur); dart_face[cur] = face_id
            rid, end = cur
            base = candidate_by_id[rid]
            vertex = base["source"] if end == 0 else base["target"]
            seq.append({"route": rid, "endpoint": end, "vertex": vertex})
            cur = phi[cur]
        faces.append(seq)

    V = len(active); E = len(edges); F = len(faces)
    genus = (2 - V + E - F) / 2.0
    if abs(genus - round(genus)) > 1e-9 or genus < 0:
        failures.append(f"invalid orientable genus result:{genus}")
    if abs(genus) > 1e-9:
        failures.append(f"non-planar port rotation system: genus={genus:g}")

    edge_faces = {rid: [dart_face.get((rid, 0)), dart_face.get((rid, 1))] for rid, _, _ in edges}
    return {
        "status": "PASS" if not failures else "FAIL",
        "plan": plan or "candidate-as-is",
        "vertices": V, "edges": E, "faces": F, "faceCount": F,
        "orientableGenus": genus,
        "rotationRoutesCW": rotation_routes,
        "rotationNeighboursCW": rotation_neighbours,
        "portDetail": port_detail,
        "faceCycles": faces,
        "edgeFaceIncidence": edge_faces,
        "allowedOverrideKeys": sorted(ALLOWED_OVERRIDE_KEYS),
        "frozenExtendIds": sorted(FROZEN_EXTEND_IDS),
        "failures": failures,
    }


def require_planar_topology(*, semantic, candidate, plans, plan) -> dict[str, Any]:
    payload = audit_topology(semantic=semantic, candidate=candidate, plans=plans, plan=plan)
    if payload["status"] != "PASS":
        raise TopologyGateError(payload)
    return payload


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--semantic", required=True)
    parser.add_argument("--candidate", required=True)
    parser.add_argument("--plans")
    parser.add_argument("--plan")
    parser.add_argument("--json-out")
    args = parser.parse_args()
    payload = audit_topology(
        semantic=args.semantic, candidate=args.candidate,
        plans=args.plans, plan=args.plan,
    )
    text = json.dumps(payload, ensure_ascii=False, indent=2)
    print(text)
    if args.json_out:
        Path(args.json_out).write_text(text, encoding="utf-8")
    return 0 if payload["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
