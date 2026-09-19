# External Route-Repair Experiment Notes

## 1. Review package reproducibility

The review package itself contains 25 files. The included focused tests reproduce 8/8 passing. The full-workspace evidence file says 51/51, but the missing workspace tests cannot be independently replayed from this ZIP alone.

The candidate remains the old unresolved geometry, so the unchanged V2 failure counts are expected.

## 2. Self-contained preplan bug

`prepare_p1_corridors.py` refers to a skeleton location outside the review package. Running it unmodified raises `FileNotFoundError`. This is a packaging/reproducibility defect, not a route-geometry defect.

The supplied patch fixes it without changing planning semantics.

## 3. Why the next planner must search target sides

Restricting Provider targets to LEFT/RIGHT made some paths unnecessarily difficult. Allowing TOP/BOTTOM produces much simpler valid local paths. Example: `A-B-06` can reach `UC-06 BOTTOM` with only one bend against the frozen Extend set.

Therefore target-side selection must be part of global planning, not a fixed legacy input.

## 4. Shared actor fan-out is a first-class resource

A sequential route can legally turn vertically immediately outside a Provider actor and then occupy the same x-coordinate across the other Provider actors' source y-ranges. That leaves later routes with zero usable source starts even though a global route is geometrically possible.

Recommended planning-only reservation:

- Provider fan-out band: x 28.0..29.9 cm, horizontal-only.
- Traveler fan-out band: x 4.4..5.6 cm, horizontal-only.

This is not a semantic model change. It is a router constraint to prevent self-inflicted port starvation.

## 5. Sequential shortest-path search is insufficient

Observed provider-only near-solution:

- 8/9 Provider Associations routed without cross-route contacts against the frozen Extend set.
- `A-CD-UC-10` remained blocked.

Single-route rip-up was insufficient: removing any one of the eight accepted Provider routes did not free a globally recoverable insertion.

Two-route removal showed the real structure:

- removing `A-PA-07` + `A-CE-09` allowed a route for `A-CD-UC-10`, but the removed pair could not both be reinserted;
- removing `A-M-UC-10` + `A-M-UC-08` also allowed a route for `A-CD-UC-10`, but the removed pair could not both be reinserted.

This means the next step is not another fixed route order. At least those interacting groups require alternate route candidates or joint batch search.

## 6. Rip-up oscillation identified

A naive algorithm that:

1. routes one shortest path;
2. identifies blockers of the next shortest path;
3. rips blockers;
4. reroutes the failed route first;

falls into a stable cycle between `A-M-UC-08` and `A-CE-09`.

This is useful negative evidence. Add a tabu/cycle detector and, on repetition, change the homotopy/corridor candidate rather than repeating the same A* cost surface.

## 7. Revised batches

The old batches are directionally useful but should not be treated as independent freezes.

Recommended mutable super-batches:

- Super-batch P (Provider lower/reversal problem): `A-M-UC-08`, `A-CE-09`, `A-PA-07`, `A-B-06`.
- Super-batch U10: `A-CD-UC-10`, `A-M-UC-10`, `A-T-UC-10`, `A-T-UC-11`.
- Traveler backbone: remaining Traveler routes, but keep them mutable until P and U10 are both feasible.
- Anchors `A-CD-UC-04` and `A-CD-UC-05` may still be preserved where compatible, but they are not sacred like the frozen Extend routes.

A route only becomes immutable after the whole official candidate passes the real gate.

## 8. Recommended alternate-path mechanism

For each route in a mutable super-batch, generate K candidates, not one:

- candidate family 1: shortest path;
- family 2: top-biased corridor;
- family 3: bottom-biased corridor;
- family 4: left/inner-biased corridor;
- family 5: right/outer-biased corridor;
- optional random deterministic tie-break seeds.

Then choose a combination that is pairwise contact-free. A small beam search over candidate combinations is preferable to rerunning one deterministic shortest path until heat death.

## 9. Exit criteria remain strict

Only the official candidate matters:

- Contact pairs = 0
- Unique contacts = 0
- crossing = 0
- overlap = 0
- T-junction = 0
- shared endpoint = 0
- short segments = 0
- redundant collinear points = 0
- V2 = PASS
- V3 = PASS
- complete workspace test suite = PASS

Anything else remains experimental.
