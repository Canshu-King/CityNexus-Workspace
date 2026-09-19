# Targeted mutation results

Result: **15/15 catastrophic mutants KILLED; 0 survivors.**

The executable runner applies one exact substitution at a time, runs its focused real regression, captures output, and restores the source in `finally`. Full diffs, commands, exit codes and killing output are in `replay_cases/mutation_results.json`.

Initial survivors exposed weak test selection rather than accepted product behavior. Two focused regressions were added in `tests/test_mutation_survivor_regressions.py`: exact cross-Journey trigger ownership and explicit mock fallback refusal during live hard capture. After rerun, both mutants were killed.

Covered classes: ACK/resolution, trigger linkage, unrelated disruption closure, provenance laundering, hard-quality allowlist, live/mock fallback, four physical-identity failure modes, C4 preservation, budget completeness, Live cursor indexing, stale-cursor fail-closed behavior, and material diff detection.
