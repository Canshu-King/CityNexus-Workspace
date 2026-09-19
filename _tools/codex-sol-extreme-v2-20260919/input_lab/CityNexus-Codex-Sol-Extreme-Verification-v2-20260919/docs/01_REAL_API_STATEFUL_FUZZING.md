# Track I — Real API stateful / property-based fuzzing

Goal:
Replace abstract-model-only confidence with production-code evidence.

Build a RuleBasedStateMachine (Hypothesis preferred) or equivalent that drives
REAL CityNexus backend endpoints on an isolated server + isolated temporary DB.

The harness must exercise actual implementation code, not a hand-written model
that re-implements the same rule it later asserts.

Actions should include, where supported by actual endpoints:
- create/reset journey
- create/generate candidate plans
- select/adopt plan
- inject/create disruption
- ACK disruption
- generate replan
- reject proposal
- accept proposal
- retry duplicate accept
- import/confirm booking
- read journey / active plan / current state
- provider/mobility failure injection
- repeated and out-of-order operations

Required invariants:
1. ACK alone never equals resolution.
2. ACCEPTED proposal resolves only its linked trigger.
3. Unrelated ACCEPTED proposal cannot close another disruption.
4. active plan has one coherent identity after accept.
5. accepted material replan materially changes itinerary unless explicitly
   classified no-alternative/protected/clarification.
6. physically closed venue cannot re-enter via alias/re-ID.
7. AMBIGUOUS physical identity is never silently promoted to SAME.
8. live-provider failure never upgrades mock/unknown mobility to hard truth.
9. hard mobility respects the exact quality allowlist.
10. protected bookings/commitments survive unless explicitly and validly changed.
11. partial budget evidence never becomes whole-trip certainty.
12. stale/nonexistent current_activity_id must fail closed, not fabricate Now.
13. final current activity has no fake Next/NextLeg.
14. repeated actions remain idempotent where contract says they should.

Deliver:
- real_api_state_machine.py
- replayable minimized failing cases
- raw run logs
- regression tests for every verified defect

Do not call a test "production-backed" unless it actually executes the real
CityNexus code path.
