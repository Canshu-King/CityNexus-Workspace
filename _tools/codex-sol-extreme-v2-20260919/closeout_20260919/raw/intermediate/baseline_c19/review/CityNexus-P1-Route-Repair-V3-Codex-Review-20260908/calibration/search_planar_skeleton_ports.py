"""Search genus-zero mutable provider port allocations around the Traveler skeleton."""
from __future__ import annotations

import copy
import json
import random
import argparse
from collections import defaultdict
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
CANDIDATE = ROOT / "visio-renderer" / "phase1-routing-rc6-candidate.yaml"
SEMANTIC = ROOT / "visio-spec" / "pages" / "p1_uc_overview.yaml"
SKELETON = ROOT.parent / "handoff_20260907" / "traveler-corridor-skeleton.yaml"
OUT = HERE / "out" / "P1-SKELETON-PLANAR-PORT-SEED.json"


def perimeter(node, side, fraction):
    l = float(node["x"]) - float(node["width"]) / 2; t = float(node["y"]) - float(node["height"]) / 2
    w = float(node["width"]); h = float(node["height"]); f = float(fraction)
    return {"TOP": f*w, "RIGHT": w+f*h, "BOTTOM": w+h+(1-f)*w, "LEFT": 2*w+h+(1-f)*h}[side]


def side_fraction(slot):
    side = ("TOP", "RIGHT", "BOTTOM", "LEFT")[slot // 12]
    # Interior grid-aligned port values. Four slots per side are enough to
    # order the incident edges without coinciding with fixed endpoints.
    return side, (slot % 12 + 1) / 13


def genus(routes, nodes):
    incidence = defaultdict(list); endpoints = {}
    for route in routes.values():
        rid = route["id"]
        for end, vertex, side, frac in ((0, route["source"], route["sourceSide"], route["sourcePortFraction"]),
                                        (1, route["target"], route["targetSide"], route["targetPortFraction"])):
            incidence[vertex].append((rid, end)); endpoints[rid, end] = (side, frac)
    sigma = {}
    for vertex, darts in incidence.items():
        order = sorted(darts, key=lambda d: (perimeter(nodes[vertex], *endpoints[d]), d))
        if any(abs(perimeter(nodes[vertex], *endpoints[a]) - perimeter(nodes[vertex], *endpoints[b])) < 1e-8
               for a, b in zip(order, order[1:])):
            return None
        for a, b in zip(order, order[1:] + order[:1]): sigma[a] = b
    alpha = {(rid, 0): (rid, 1) for rid in routes}
    alpha.update({(rid, 1): (rid, 0) for rid in routes})
    phi = {dart: sigma[alpha[dart]] for dart in alpha}
    seen = set(); faces = 0
    for dart in phi:
        if dart in seen: continue
        faces += 1; current = dart
        while current not in seen:
            seen.add(current); current = phi[current]
    return (2 - len(incidence) + len(routes) - faces) / 2


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--force-right", action="append", default=[], help="provider route id constrained to a RIGHT target port")
    parser.add_argument("--force-side", action="append", default=[], help="routeId=LEFT|RIGHT|TOP|BOTTOM target constraint")
    args = parser.parse_args()
    forced_side = dict(item.split("=", 1) for item in args.force_side)
    candidate = yaml.safe_load(CANDIDATE.read_text(encoding="utf-8"))
    skeleton = yaml.safe_load(SKELETON.read_text(encoding="utf-8"))
    semantic = yaml.safe_load(SEMANTIC.read_text(encoding="utf-8"))
    nodes = {n["id"]: n for n in semantic["shapes"] if n["id"] != "BOUNDARY"}
    base = {r["id"]: copy.deepcopy(r) for r in candidate["routes"]}
    skeleton_routes = {r["id"]: r for r in skeleton["routes"]}
    for rid, route in skeleton_routes.items():
        for key in ("sourcePortFraction", "targetSide", "targetPortFraction"):
            base[rid][key] = route[key]
    providers = [rid for rid, route in base.items() if route["connectorType"] == "association" and route["family"] == "provider"]
    provider_targets = defaultdict(list); provider_sources = defaultdict(list)
    for rid in providers:
        provider_targets[base[rid]["target"]].append(rid); provider_sources[base[rid]["source"]].append(rid)
    rng = random.Random(20260907)
    slots = list(range(48))
    for trial in range(250000):
        routes = copy.deepcopy(base)
        # A provider actor only exposes left-side source ports.  Distinct
        # fractions permute the local rotation while retaining external-side
        # semantics.
        for vertex, ids in provider_sources.items():
            fractions = [(i + 1) / (len(ids) + 1) for i in range(len(ids))]
            rng.shuffle(fractions)
            for rid, fraction in zip(ids, fractions): routes[rid]["sourcePortFraction"] = fraction
        for vertex, ids in provider_targets.items():
            fixed_slots = []
            for route in routes.values():
                if route["target"] != vertex or route["id"] in ids:
                    continue
                value = perimeter(nodes[vertex], route["targetSide"], route["targetPortFraction"])
                fixed_slots.append(value)
            rng.shuffle(slots)
            used = []
            for rid in ids:
                for slot in slots:
                    side, fraction = side_fraction(slot)
                    if rid in args.force_right and side != "RIGHT":
                        continue
                    if rid in forced_side and side != forced_side[rid]:
                        continue
                    value = perimeter(nodes[vertex], side, fraction)
                    if all(abs(value - other) > 0.05 for other in [*fixed_slots, *used]):
                        routes[rid]["targetSide"] = side; routes[rid]["targetPortFraction"] = fraction
                        used.append(value); break
        g = genus(routes, nodes)
        if g == 0:
            overrides = {rid: {key: routes[rid][key] for key in ("sourcePortFraction", "targetSide", "targetPortFraction")}
                         for rid in providers}
            payload = {"status": "PASS", "trial": trial, "genus": g, "providerOverrides": overrides,
                       "travelerSkeletonOverrides": {rid: {key: route[key] for key in ("sourcePortFraction", "targetSide", "targetPortFraction")}
                                                     for rid, route in skeleton_routes.items()}}
            OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
            print(json.dumps(payload, ensure_ascii=False, indent=2)); return 0
    payload = {"status": "FAIL", "trials": 250000}
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(payload)); return 2


if __name__ == "__main__":
    raise SystemExit(main())
