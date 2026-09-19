# Post-v3 integration plan

This document is NOT permission for Qoder to touch the main tree.

If and only if independent review accepts v3:

## Gate A — freeze authoritative CityNexus baseline
Owner/maintainer action:
- create a real Git baseline for current `D:\moodle\CityNexus`;
- exclude `.env`, API keys, DBs, caches, node_modules, generated runtime junk;
- tag/commit the exact current source state.

## Gate B — reconcile Qoder patch
Do not assume synthetic baseline `c6f9024` is the real merge base.

Manually reconcile/cherry-pick equivalent changes onto an integration branch.

## Gate C — authoritative tests
Run on integrated source:
- T1–T4 focused tests
- replan/guardian/booking truth tests
- `npm run typecheck`
- `npm run build`
- rendered Today/Live checks

## Gate D — routing provider
For a Xiaomi trial that includes dynamic auto-replan:
configure a trustworthy routing source using the existing live routing path.

If no trustworthy routing source is available:
auto-replan must remain truth-safe unavailable rather than fabricate travel time.

## Gate E — fresh Xiaomi trace
One fresh same-Xiamen journey:
create -> plan -> hotel -> booking -> map -> Copilot -> mutable closure ->
provider-backed material replan -> UI accept -> final Today/Trips/Live agreement.

Frontend vNext starts only after this gate.
