# F3 Opportunity Window Integration

Current checkpoint problem: `F3_WINDOW_REPLACEMENT` is only the second ranked same-slot replacement. The public family name therefore overstates the implementation.

## Target semantics

F3 must use verified facts:

```text
window opens
+ inbound travel
+ visit duration
+ outbound travel to next protected commitment
+ safety buffer
+ opening hours
+ budget
→ fit / reject
```

Use the prepared module:

`backend/app/replanning/opportunity_window_family.py`

## Recommended integration

For a closure/weather disruption on a future flexible Activity:

1. Find the next active C4 anchor after the disrupted slot.
2. Use the disrupted Activity start time (or later verified execution time) as the window opening time.
3. Determine previous/current semantic location.
4. Determine candidate Place opening interval from authoritative Place data.
5. Obtain inbound/outbound minutes from the current deterministic mobility source or frozen MobilitySnapshot.
6. Evaluate with `evaluate_window_replacement()`.
7. Only create F3 from a `fits=True` result.
8. Persist evidence into `ReplanDiff`, e.g.:
   - `window_opens_at`
   - `next_commitment_start`
   - `remaining_buffer_min`
   - `inbound_travel_min`
   - `outbound_travel_min`
   - `safety_buffer_min`
9. Build the candidate PlanVersion.
10. Run the full authoritative feasibility gate again.

## Important travel rule

The evaluator intentionally creates its OpportunityWindow with `travel_to_commitment_min=0`, because the candidate itself supplies `outbound_travel_min`. Do not subtract the outbound leg twice.

## Scoring

Only after real F3 evidence exists should `opportunity_value` cease using the neutral fallback. A conservative first rule is acceptable, but it must be documented and derived from actual window evidence, not LLM output or arbitrary visit duration.

## Gate tests

- candidate fits with sufficient buffer -> F3 created;
- candidate misses next C4 after outbound travel -> no F3;
- candidate closes before visit ends -> no F3;
- candidate exceeds remaining budget -> no F3;
- C4 start remains exactly preserved;
- full plan feasibility must still pass.
