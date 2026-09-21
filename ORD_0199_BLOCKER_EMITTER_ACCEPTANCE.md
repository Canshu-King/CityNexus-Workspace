# ORD-0199 Mobility Blocker Emitter Acceptance

Purpose: make the first real mobility-evidence blocker a stable product truth without contaminating the separate P7 resolver-integration gate.

## 1. Gate ownership

`ORD-0199` stays P0 for Operation Anywhere Sunrise because the milestone is not merely 'planner rejected'; it is 'the first real blocker is named accurately'.

However, `P7_RESOLVER_INTEGRATED` remains a resolver/product-integration claim. ORD-0199 is NOT an additional P7 condition and should not be added to `p7_check.py`.

Both may therefore be true at the same time:

```text
P7_RESOLVER_INTEGRATED = true
ORD-0199_BLOCKER_EMITTER = false
```

In that state, the wake sequence may proceed to the exact-P7 canary, where the missing named blocker is a real downstream product finding.

## 2. Named blocker is required, exact literal is not sacred

The product must emit a stable machine-readable reason when a candidate is rejected specifically because one or more actually used mobility edges are not hard-eligible.

Preferred canonical code:

`MOBILITY_EVIDENCE_NOT_HARD_ELIGIBLE`

If an existing stable server projection already has a reason-code namespace, use that namespace rather than inventing a parallel field. The acceptance condition is semantic and machine-readable, not UI-string matching.

Human-facing copy may vary.

## 3. Emission preconditions

Emit the mobility blocker only when all of these hold:

```text
a concrete candidate was evaluated
candidate.used_edge_ids is non-empty
at least one used edge has hard_eligible = false
the planner rejection is caused by that used-edge evidence deficiency
```

Receipt must bind:

```text
candidate_id
used_edge_ids
per_edge_source_kind
per_edge_provider_or_fixture
per_edge_fact_quality
per_edge_hard_eligible
first_blocking_edge_or_edges
blocker_basis = USED_EDGE_INVENTORY
aggregate_repository_counts_used_as_blocker = false
blocker_reason = MOBILITY_EVIDENCE_NOT_HARD_ELIGIBLE
selectable_emitted = false
```

## 4. Forbidden emissions

Do NOT emit this reason for:

- provider/runtime failure;
- malformed provider evidence;
- unresolved or ambiguous destination identity;
- hydration/catalog failure before candidate evaluation;
- empty candidate set with no used-edge inventory;
- repository-wide aggregate synthetic counts;
- a candidate whose actual used edges are all hard-eligible.

These must retain their own earlier-stage reason.

## 5. Bidirectional behavioral gates

### Positive gate

Given a candidate whose actual used-edge inventory contains a non-hard-eligible edge:

```text
planner rejects candidate
reason == MOBILITY_EVIDENCE_NOT_HARD_ELIGIBLE
selectable_emitted == false
blocker_basis == USED_EDGE_INVENTORY
```

Deleting/bypassing the emitter must make this gate red.

### Negative gate

Given the same candidate shape but every actually used edge is hard-eligible:

```text
reason != MOBILITY_EVIDENCE_NOT_HARD_ELIGIBLE
planner continues normal evaluation
```

Forcing the reason unconditionally must make this gate red.

## 6. Earliest-blocker precedence

If an earlier stage already has a truthful blocking state, do not overwrite it with the mobility reason.

Examples:

```text
provider runtime failure -> resolver reason wins
malformed provider evidence -> malformed-evidence reason wins
identity unresolved/ambiguous -> identity reason wins
hydration/catalog failed before candidate evaluation -> hydration/catalog reason wins
candidate evaluated + used edge not hard-eligible -> mobility reason wins
```

This preserves the rule: report the first real blocker, not merely the last code path touched.

## 7. Morning-report state

Until the emitter exists and is independently reproduced:

`MOBILITY_GAP_OBJECTIVE = REPRODUCED` may be true if the used-edge facts were reproduced, while:

`NAMED_BLOCKER_PRODUCT_EMISSION = PENDING(emitter missing)` remains true.

Do not collapse those two cells.

## 8. Frozen rule

> The named blocker is part of the product truth contract for Operation Anywhere Sunrise, but it is not part of the P7 resolver gate.