# CityNexus P1 Topology + Planner Review Assist

External assistance prepared after auditing `CityNexus-P1-Topology-and-Planner-GPT-Opinion-Review-20260907-GPT.zip`.

This package does **not** contain or claim a passing official route candidate. It gives Codex: 

- a hardened topology pre-gate (`patches/audit_p1_route_topology_v2.py`);
- exact critical-coordinate collision helpers (`patches/critical_grid_geometry.py`);
- an exact conflict-aware candidate-family selector (`patches/route_candidate_selector.py`);
- focused contract tests for those helpers;
- PLAN_O-first route-family seeds;
- reproduced topology and validator evidence;
- a concrete next execution instruction.

Read `REVIEW-FINDINGS.md` first, then `CODEX_NEXT_INSTRUCTION.md`.

Frozen project constraints remain unchanged: C1-C4 stay frozen, the three Extend routes are immutable, validators must not be weakened, and formal Visio/RC6/Part 2/codex-chatgpt-web remain blocked until a full V2/V3/pytest pass is externally reviewed.
