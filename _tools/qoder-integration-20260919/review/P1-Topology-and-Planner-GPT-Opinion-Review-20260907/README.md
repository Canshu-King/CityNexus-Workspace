# CityNexus P1 Topology and Planner Review Package

This package asks for an external engineering review of the still-unresolved
P1_UC_Overview Association route repair. It records an independently reproduced
topology blocker and a complementary bounded-planner aid. It is not a release
or a claim that the official candidate has passed geometry validation.

Read `GPT-OPINION.md` first, then `AUDIT-RESULT.md`. The current official
candidate and semantic source are under `current/`. Reproduction evidence is
under `evidence/`; the two external inputs are preserved under `inputs/`.

The official candidate was copied into this package after its SHA-256 was
recorded. No experiment in this package writes back to it.

The required repair pipeline is:

`port allocation search -> topology pre-gate -> planar face scaffold -> global
orthogonal routing -> negotiated congestion / rip-up / backtracking -> path
normalization -> existing Base Gate -> Contact Audit -> V2 -> V3 -> pytest`

Frozen constraints remain:

- `EXT-07-06`, `EXT-09-08`, and `EXT-10-09` are immutable, including all
  fields and geometry.
- Association identity (`id`, `connectorType`, `source`, and `target`) is
  immutable.
- Validators must not be weakened.
- Do not render Visio, promote RC6, or start Part 2.

Only the first candidate that reaches zero defects, V2 PASS, V3 PASS, and a
zero-failure complete test suite may update the official candidate or status.
