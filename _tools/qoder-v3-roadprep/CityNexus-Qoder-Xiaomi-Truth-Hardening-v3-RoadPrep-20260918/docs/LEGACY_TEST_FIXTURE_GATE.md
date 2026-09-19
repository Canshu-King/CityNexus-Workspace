# Legacy test fixture gate

The old tests may be repaired, but the current complete-graph helper is too
powerful.

## Current problem

`_qoder_explicit_demo_mobility.py`:
- creates every ordered demo-place pair;
- uses one invented 15-minute value;
- is autouse across entire test modules.

That can silently convert "missing mobility" into "known mobility" far outside
the 12 tests that motivated the change.

## Required replacement

Provide an explicit helper such as:

`seed_explicit_mobility(monkeypatch, {("A","B"): 20, ...})`

Rules:
- exact pair list supplied by the scenario/test;
- exact duration supplied by the scenario/test;
- no complete graph;
- no global universal 15;
- no module-wide autouse unless every test in that module intentionally needs
  the same explicit matrix;
- a pair not listed stays missing/synthetic.

Prefer test-local fixtures or scenario builders.

## Required sentinel regression

Within a module that uses explicit test mobility:
- seeded pair is hard-eligible;
- unseeded pair remains unavailable.

This proves the helper has not neutralized B1.
