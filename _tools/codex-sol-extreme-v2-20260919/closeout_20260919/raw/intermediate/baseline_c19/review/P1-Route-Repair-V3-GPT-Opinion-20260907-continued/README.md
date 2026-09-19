# CityNexus P1 Route Repair V3 - GPT Review Package

This package is an external-review handoff for the unresolved P1 route repair.

Review order:

1. Read GPT-OPINION.md and AUDIT-RESULT.md.
2. Inspect the current candidate and semantic source under visio-spec/.
3. Inspect validators, conflict reports, preplanning outputs, and tests under visio-renderer/.
4. Treat traveler-corridor-skeleton.yaml only as a verified Traveler sub-solution and corridor reference. Do not overwrite the complete candidate with it.

Hard constraints:

- Preserve EXT-07-06, EXT-09-08, and EXT-10-09 exactly, including fields and geometry.
- Do not weaken any validator.
- Use global port/corridor planning with batched rip-up and reroute.
- Do not render Visio, promote RC6, or begin Part 2.
- Status may be advanced only after Contact, short segment, and redundant collinear counts are all zero, V2 and V3 pass, and the complete test suite passes.

Current state: the workspace test suite passes 51/51, but the official route candidate remains geometrically unresolved and V2/V3 remain FAIL.
