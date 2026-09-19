# Track M — Mobility truth taint / laundering proof

Goal:
Prove there is no path where weak/synthetic/unknown mobility evidence becomes
hard feasibility truth.

Treat fact-quality as a taint lattice:
- HARD_ALLOWED: explicitly approved qualities only
- SOFT/UNKNOWN
- SYNTHETIC/MOCK
- UNAVAILABLE/FAILED

Trace both statically and dynamically through:
provider adapter -> runtime capture -> snapshot normalization -> storage/evidence
-> candidate evaluation -> replan endpoint -> UI/API projection.

High-risk questions:
- Can provenance strings re-promote unknown facts?
- Can fallback output inherit a trusted provider name?
- Can serialization/deserialization drop `fact_quality` and later infer trust?
- Can mixed snapshots make one hard leg bless another weak leg?
- Can legacy replay labels become trusted without explicit quality?
- Can cached/stale mobility keep hard eligibility after provider failure?

Deliver:
- mobility_taint_graph.json
- MOBILITY_TAINT_PROOF.md
- laundering_repros/
- focused tests for any reachable laundering path

Do not infer hard truth from provider name alone.
