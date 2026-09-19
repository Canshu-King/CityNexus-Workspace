# CityNexus P1 Route Repair - Deep Assist Findings

Date: 2026-09-08
Scope: P1_UC_Overview route-planning workbench only.

## 1. Safety / baseline

The authoritative routing candidate was not edited by this assist work.

- source Codex review ZIP SHA-256: `941765ab65b2015e5f8641338e71bfd0d29bb6573501cdbfb1544365c3ea090b`
- authoritative candidate SHA-256: `8c1661ebb1a9d5a371f48ef800316dd643f391beec559eb2a4b8065eed75182d`
- metadata status remains `PLANNING_REQUIRED`
- `EXT-07-06`, `EXT-09-08`, `EXT-10-09` remain `FROZEN_FROM_C4E1` and unchanged.

Current official geometry remains blocked:

- V1/base gate: PASS
- V2: FAIL
- V3: FAIL only because V2 FAIL; V3 own failures remain empty
- contactPairCount: 46
- uniqueContactCount: 55
- T-junctions: 22
- shared endpoints: 33
- short segments: 9
- redundant collinear points: 88
- newly-audited self contacts on current candidate: 0

No result in this assist package is a formal RC6 candidate.

## 2. Runtime topology interlock added

The topology audit is now importable and is wired into the common route loader.
Any solver using `route_p1_negotiated_grid.load()` rejects a non-planar port
rotation before path search.

Reproduced:

- `PLAN_TRAVELER_SKELETON_PROVIDER_GRID`: genus 1 -> immediate `TopologyGateError`
- `PLAN_TRAVELER_SKELETON_PLANAR_GRID`: genus 0 -> PASS

This closes the failure mode that allowed expensive candidate/CP-SAT runs on a
mathematically non-planar endpoint rotation.

## 3. Self-contact gate added

The previous contact audit checked only route-vs-route contacts. It did not
reject one Association that crosses, overlaps, retraces, or T-junctions with
itself.

The updated contact gate now emits:

- `selfContactCount`
- `selfContactCounts`
- `selfContacts`

and V2 fails if any non-adjacent self contact exists. Current authoritative
candidate has selfContactCount=0, so this adds protection without changing the
existing reason for failure.

The candidate selector independently rejects self-contacting polylines as well.

## 4. Candidate-pool feasibility prechecks

The candidate selector now provides two cheap proofs before any expensive
optimization:

1. route-pair compatibility: if any route pair has zero compatible candidate
   pairs, the current discrete pool cannot possibly produce 18/18;
2. AC-3 pruning: if a route domain becomes empty after pairwise support
   propagation, the current pool is infeasible even when every route pair is
   separately compatible.

A cheap MRV + least-constraining-value feasibility solver was also added so a
complete witness can be found without OR-Tools when the discrete pool is
already viable.

## 5. Genus-0 pool experiment: the bottleneck is candidate-family coverage

On `PLAN_TRAVELER_SKELETON_PLANAR_GRID`, a reproducible 12-sample pool produced:

- candidateCount: 143
- conflictPairCount: 3064
- topology: PASS, genus 0

The pool had five route pairs with zero compatible candidate pairs:

- `A-CD-UC-04` / `A-CD-UC-10`
- `A-CD-UC-10` / `A-M-UC-04`
- `A-CD-UC-10` / `A-B-06`
- `A-M-UC-10` / `A-B-06`
- `A-B-06` / `A-PA-07`

`A-T-UC-07` / `A-PA-07` was very tight (2 compatible pairs out of 63).

This means more CP-SAT time on that pool would be pointless. The search space
must first gain missing homotopy families.

## 6. Targeted pair-family synthesis works

A new helper can freeze one sampled candidate of route A as an exact obstacle
and reroute route B, then reverse the direction. This produced pairwise
compatible constructions for the five core zero-compatibility pairs above,
and also for `A-T-UC-10` / `A-CE-09`.

Examples are included in `evidence/pair_*.json`.

Important limitation: these PASS results prove pairwise separability only for
the sampled port plan/family search. They do NOT prove a global 18-route
embedding.

The small `A-T-UC-07` / `A-PA-07` targeted sample did not find a compatible
pair, while the larger 12-sample pool already contained 2 compatible pairs.
Therefore this pair is tight, not proven impossible.

## 7. Automatic pair-gap repair removes pairwise dead pairs, then AC-3 finds the next real blocker

The upgraded pool explorer can automatically synthesize missing families for
all zero-compatibility route pairs.

In a reproduced repaired pool:

- all route pairs obtained at least one compatible pair;
- poolFeasibilityPrecheck became PASS;
- AC-3 still failed because `A-T-UC-07` lost its complete domain.

The last-support failures concentrated around:

- `A-T-UC-06`
- `A-B-06`
- `A-PA-07`
- sometimes `A-T-UC-11`

This is a higher-order bundle problem. The next useful search is not another
full-page random run; it is a topology-safe local port/family search around the
UC-06 / UC-07 cluster, then reintegration into all 18 Associations.

## 8. Higher-order bundle repair added

`explore_p1_disjoint_pool.py` now has an AC-3 empty-domain repair pass. It
identifies dominant blocker routes, freezes mutually compatible blocker
candidates as a bundle, then reroutes the empty route against both at once.

A small first run did not repair `A-T-UC-07`, which is useful evidence: the
existing endpoint allocation/candidate families are still too restrictive.
The script records these failures instead of hiding them behind repeated random
search.

## 9. New local port-search workbench

`search_p1_local_bundle_ports.py` was added for the recurring hard bundle:

- `A-T-UC-06`
- `A-T-UC-07`
- `A-T-UC-11`
- `A-B-06`
- `A-PA-07`

It:

1. starts only from the proven genus-0 plan;
2. enumerates strategic target-port variants for T06/B06/PA07;
3. rejects every full rotation with genus != 0;
4. generates candidate families;
5. injects matching validated Traveler-skeleton paths as optional candidates,
   never as immutable obstacles;
6. performs pair-gap repair;
7. performs AC-3 and optional bundle repair;
8. runs the exact MRV feasibility selector only after the pool passes cheap
   prechecks;
9. never modifies the authoritative candidate.

A short smoke search tested three genus-0 variants. All pairwise dead pairs
could be repaired, but AC-3 still emptied one route (`A-B-06` or
`A-T-UC-06`). This is a diagnostic result, not a failure of the project: it
narrows the next search to port allocation / higher-order corridor families.

## 10. Useful geometric observation around UC-06

`EXT-07-06` forms a long U-shaped immutable barrier around the UC-06 region:

- horizontal y=6.6 from x=17.2 to x=8.3
- vertical x=8.3 down to y=9.7
- horizontal y=9.7 to x=11.1
- terminal to UC-06 bottom

The existing Traveler T06 skeleton therefore approaches UC-06 by going below
that U and coming back through the right-hand corridor. Booking-to-UC06 also
needs access from the provider/right side. This explains why `A-T-UC-06` and
`A-B-06` repeatedly become higher-order blockers: they compete for a narrow
region constrained by a frozen Extend, not merely by bad random A* tie breaks.

Do not assume “Traveler should enter UC-06 from LEFT” is automatically better.
That port is reachable only through a substantial detour around the frozen U,
and sampled local searches did not make the bundle consistent.

## 11. Review-package reproducibility fixes

The helper scripts no longer silently depend on
`handoff_20260907/traveler-corridor-skeleton.yaml`.

Relevant scripts now accept an explicit `--traveler-skeleton` path.

The relaxed CP-SAT diagnostic label was corrected conceptually:
`bestObservedDisjointSubset` is used unless optimality is actually proven, and
solver status/objective/bound data are surfaced when OR-Tools is available.

## 12. Test state

After all patches in this assist package:

- pytest: 23 passed
- Python compileall: PASS
- invalid genus-1 plan interlock: PASS (rejected)
- valid genus-0 plan interlock: PASS
- current V2/V3 failure counts remain unchanged except for the new explicit
  self-contact count, which is zero.

## 13. Recommended next technical target

Do NOT return to broad random full-18 search yet.

First obtain a local contact-free witness for the UC-06/UC-07 five-route bundle
under a genus-0 endpoint rotation. If the current strategic search keeps
emptying T06/T07/B06, broaden target-side/target-fraction search for those
routes (and only then source fractions), while preserving the full rotation
system genus=0.

Once a local witness exists:

1. convert its port changes into a new EXPERIMENTAL port-plan seed;
2. audit full topology (genus 0 required);
3. run the full 18-route candidate pool with the local winner injected as
   optional candidates, not frozen truth;
4. pair-precheck -> AC-3 -> MRV/CP-SAT;
5. only an actual 18/18 candidate may proceed to normalization, V1, contact
   audit, V2, V3, and full pytest.

First all-green result must STOP for external review. No formal Visio render,
RC6 promotion, P1 Domain Overview, Part 2, or codex-chatgpt-web in the same run.
