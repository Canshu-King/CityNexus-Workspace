# Opportunity Window + Feasibility Envelope

These are high-value CityNexus concepts and should be implemented as **derived data**, not new authoritative entities.

## OpportunityWindow

Derived from:
- current timestamp/current activity end;
- next protected/locked commitment;
- travel estimate to that commitment;
- safety buffer.

```text
available_minutes =
next_commitment_start
- current_time
- travel_to_commitment
- safety_buffer
```

Candidate opportunity must still pass normal deterministic checks:
- open at visit time;
- duration fits;
- inbound/outbound travel fits;
- budget fits;
- does not endanger protected commitments.

## FeasibilityEnvelope

Expose how robust a feasible plan is, for example:
- next commitment buffer minutes;
- journey-end slack minutes;
- budget remaining minor units;
- provider degradation list;
- preserved commitment count;
- risk reason codes.

This gives the UI a truthful answer to “how safe is this plan?” rather than a mysterious percentage.
