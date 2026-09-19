# Playwright Golden Scenario

The final E2E should prove the CityNexus product thesis, not merely that buttons are clickable.

## Golden scenario

1. Reset deterministic demo.
2. Generate and select Balanced Plan.
3. Create River Cruise booking.
4. Capture payment.
5. Verify C4/lock evidence.
6. Start Journey.
7. Inject Tech Art Center closure with Demo Event Simulator.
8. Generate feasible replan candidates.
9. Compare Before/After.
10. Assert:
   - Tech Art removed;
   - replacement added;
   - River Cruise preserved at 15:30;
   - protected commitment count unchanged;
   - score/diff/envelope visible;
11. Accept replan using idempotency key.
12. Verify new PlanVersion ACTIVE and old plan SUPERSEDED.
13. Refresh page and verify JourneyTwin reproduces the accepted state.

## Second resilience scenario

- simulate Valhalla unavailable;
- verify JourneyTwin DEGRADED and explicit fallback evidence;
- core deterministic demo must still work.

## Third AI scenario

- primary AI disabled/failing;
- deterministic explanation remains available;
- no core workflow failure.
