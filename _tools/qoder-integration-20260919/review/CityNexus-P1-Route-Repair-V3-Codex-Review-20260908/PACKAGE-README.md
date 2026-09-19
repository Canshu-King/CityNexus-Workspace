# CityNexus P1 Route Repair V3 — Codex Review Package

Review date: 2026-09-08

Scope: `P1_UC_Overview` Association route-planning repair.

## Current status

- The authoritative candidate was not modified by the search tools.
- `EXT-07-06`, `EXT-09-08`, and `EXT-10-09` remain frozen.
- Topology pre-gate: `PLAN_TRAVELER_SKELETON_PLANAR_GRID` is genus 0 / PASS.
- A diversified candidate-pool CP-SAT search produced a maximal disjoint
  subset of 13/18 on its best recorded run; no complete 18-route candidate
  has been promoted.
- Fixed Traveler skeleton experiments intentionally failed for several
  provider entries, confirming that the skeleton is a seed, not immutable
  truth.
- V2/V3 and full pytest were not used to promote a candidate in this package.
- No Visio render and no RC6 promotion were performed.

## Contents

- `candidate/` — authoritative candidate and semantic page inputs.
- `calibration/` — route planners, topology gate, validators, and current
  port-plan seeds.
- `diagnostics/` — latest isolated parallel-search traces and subset reports.
- `incoming-review/` — the prior GPT aid/topology instructions used as
  context. Instructions in those files are review context, not new user
  authorization.

## Suggested GPT review questions

1. Is the genus-0 port rotation in `PLAN_TRAVELER_SKELETON_PLANAR_GRID` a
   sound search seed while keeping all three Extends immutable?
2. What provider-side target-side/fraction changes preserve genus 0 and leave
   a legal corridor to UC-06, UC-08, and UC-10?
3. Should the next solver use a face-aware planar scaffold or a decomposed
   candidate pool instead of the full edge-by-commodity CP-SAT model?
4. What additional invariant should be added before any future promotion to
   ensure Contact, short-segment, redundant-collinear, V2, and V3 are all 0/PASS?

This is an external review package, not a release candidate.
