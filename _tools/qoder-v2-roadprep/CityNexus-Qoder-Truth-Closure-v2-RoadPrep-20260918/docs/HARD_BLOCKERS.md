# Hard Blockers Before Merge

## B1 — real replan path must reject fabricated mobility facts

The fix must cover the actual `/replans` execution path, not only the strict
provider primitive.

Required:
- no replan hard-feasibility decision may consume the blanket mock default 20;
- previously frozen synthetic-default facts must not silently become hard truth;
- missing mobility must be candidate-specific and fail closed;
- a valid candidate must still be allowed if another candidate has unavailable
  mobility.

## B2 — T1 replacement identity must be fail-safe across providers

Required:
- SAME means proven same;
- DIFFERENT means evidence supports different;
- AMBIGUOUS means cannot safely distinguish;
- replacement exclusion excludes SAME and AMBIGUOUS;
- the generic `is_same_physical_venue()` helper must not pretend AMBIGUOUS is
  literally SAME.

## B3 — ACK semantics need real UI integration proof

Required:
- ACKNOWLEDGED + no linked accepted replan remains actionable in Today and Live;
- matching ACCEPTED replan closes it in both;
- unrelated ACCEPTED proposal does not close it;
- no impossible/dead acknowledged-only UI branch.

## B4 — budget verdict must describe its real scope

A global "budget verified" claim requires all budget-relevant components.

At minimum consider:
- activity/attraction costs;
- selected stay/hotel if it is part of the trip;
- confirmed transport/booking amounts if they are part of the trip budget.

If the product cannot aggregate these reliably yet:
- do NOT claim total trip budget verified;
- say `活动费用已完整` / `已知部分 ¥X` instead.

## B5 — integration baseline

Before merging:
- freeze the authoritative current CityNexus source into a real Git baseline;
- exclude secrets, runtime databases, node_modules, caches and generated junk;
- apply/reconcile the Qoder patch against that frozen baseline;
- run tests on the authoritative integration branch.

The synthetic Qoder commit `c6f9024` is not itself the authoritative merge base.
