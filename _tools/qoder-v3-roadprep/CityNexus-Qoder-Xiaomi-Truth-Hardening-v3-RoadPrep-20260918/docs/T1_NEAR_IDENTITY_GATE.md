# T1 near-identity gate

Keep v2's:
- SAME / DIFFERENT / AMBIGUOUS;
- explicit wrapper relation;
- provider-scoped identities;
- SAME-only `is_same_physical_venue`;
- SAME+AMBIGUOUS replacement exclusion.

Add near-coordinate cross-provider handling.

## Required behavior

For different provider identities:

same normalized venue name
+ compatible category
+ coordinates within a conservative near-distance threshold
=> AMBIGUOUS, not DIFFERENT.

Use real geographic distance rather than equality of rounded tuples if
practical.

Address/building/provider metadata may strengthen the decision when available.

Do NOT turn proximity alone into SAME.

## Regressions

1. same venue across providers, ~5–20m coordinate drift -> AMBIGUOUS / excluded
2. same name/category but clearly far apart -> DIFFERENT
3. different names in same building -> DIFFERENT
4. same chain name but separate branches beyond threshold -> DIFFERENT
5. wrapper/provider structural identity remains SAME
