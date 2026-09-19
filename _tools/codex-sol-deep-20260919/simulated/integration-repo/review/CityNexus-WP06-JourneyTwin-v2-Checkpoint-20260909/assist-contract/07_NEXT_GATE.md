# Next external checkpoint gate

Do not judge success by a specific test count if Codex adds more tests. All tests must pass.

Minimum evidence for the next deterministic-WP06 checkpoint:

1. all prior 104 tests remain green;
2. all 11 prepared integrity/provider-snapshot regressions pass;
3. JourneyTwin persists after start/complete;
4. ACTIVE Journey cannot be mutated into infeasibility silently;
5. cross-Journey Event cannot trigger Replanning;
6. Replanning only follows the declared Journey/Plan state policy;
7. current activity belongs to the newly active plan after acceptance;
8. active C4 commerce Commitment is enforced at proposal generation and acceptance;
9. canonical Tech Art closure produces a changed proposal;
10. proposal removes Tech Art and adds a valid alternative;
11. River Cruise 15:30 C4 is unchanged;
12. ReplanDiff reflects the real change;
13. raw live provider objects remain forbidden inside the feasibility gate;
14. frozen mobility snapshot facts are accepted deterministically;
15. no real external service is mandatory for the default demo.

On the reconstructed checkpoint + prepared patch, the combined suite is **115 passed** and compileall passes.
