# T3/T4 Integration Gate

## T3 — ACK vs resolution

Fix the dead condition.

An ACKNOWLEDGED-only event is still open, so traveler copy may say:

`已知晓，仍待处理`

while the event remains in the active/open set.

Required UI integration cases:

1. ACK only:
   - Today shows one unresolved change;
   - Live shows the disruption as unresolved;
   - traveler sees "已知晓，仍待处理" or equivalent.

2. matching ACCEPTED proposal:
   - Today no longer escalates it;
   - Live shows handled;
   - refresh preserves this.

3. unrelated ACCEPTED proposal:
   - event remains open.

The test must render the real components/page. A `page.evaluate(import helper)`
test is useful unit coverage but is not sufficient as integration proof.

## T4 — Budget evidence

First decide the claim scope.

### Preferred
Build a `TripBudgetEvidence` aggregator from all currently available
budget-relevant sources:
- activities;
- selected stay/hotel;
- confirmed booking/transport amounts.

Then classify total coverage NONE / PARTIAL / FULL.

### Safe fallback
If full trip aggregation is not available in this round:
- rename the claim to activity-cost coverage;
- never show "trip budget verified".

## Evidence quality

Do not treat a positive amount with no status/provenance as automatically
verified.

Prefer:
- KNOWN_FREE
- KNOWN_PAID / KNOWN
as verified.

Treat statusless legacy amounts as estimated/partial unless provenance proves
otherwise.

## Required tests

1. all activities known, hotel unknown -> trip budget remains PARTIAL
2. hotel known, transport booking unknown -> remains PARTIAL if transport is in scope
3. KNOWN_FREE -> known
4. positive amount without reliable status -> does not create FULL verification
5. actual UI does not show total budget verdict for PARTIAL
6. FULL only after every required component is known
