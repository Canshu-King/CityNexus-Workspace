# Request for GPT External Opinion

## Decision Requested

Review the supplied P1 Route Repair V3 evidence and propose a concrete global port/corridor allocation and batched reroute plan that can bring the official candidate to zero contacts, zero short segments, and zero redundant collinear points without changing the three frozen Extend routes or weakening validation.

## Established Facts

- Complete local workspace test suite: 51 passed, 0 failed.
- The official candidate is still unresolved.
- Current V2 diagnostics: contactPairCount 46; uniqueContactCount 55; tjunction 22; shared_endpoint 33; shortSegmentCount 9; redundantCollinearPointCount 88.
- V3 fails because the underlying V2 geometry gate fails; frozen-route protection passes.
- traveler-corridor-skeleton.yaml is a verified sub-solution for nine Traveler Association routes plus the three frozen Extend routes. It is reference material, not a complete replacement candidate.
- A-CD-UC-04 and A-CD-UC-05 currently have zero contacts and should be preserved where compatible with the global solution.
- Sequential local A-star experiments stalled under different route orders, so worklist priority is not a route-freezing order.

## Recommended Planning Frame

Plan all ports and corridors first, then reroute in batches with rip-up allowed inside each affected batch:

- Batch A: Traveler corridor skeleton integration.
- Batch B: UC-10 central/provider routes: A-CD-UC-10, A-M-UC-10, A-T-UC-10, A-T-UC-11.
- Batch C: Booking/Payment routes: A-B-06 and A-PA-07.
- Batch D: Mobility/Context routes, including A-M-UC-08 and A-CE-09.
- Batch E: anchor compatibility and final cleanup.

Useful but non-binding corridor references:

- A-T-UC-06 can enter UC-06 from RIGHT.
- A-T-UC-08 can use the right half of UC-08 BOTTOM.
- A-T-UC-10 can approach UC-10 LEFT through the central corridor near y=10.1.
- A-T-UC-12 can use the lower corridor.

## Review Questions

1. Is the batch partition globally viable, or should routes move between batches?
2. Which exact ports and shared corridor bands should be reserved before drawing any route?
3. Which routes must be ripped up together to avoid the observed sequential-search dead ends?
4. Are there hidden topological constraints that make the abstract planar preplan geometrically unrealizable?
5. Provide a concrete next-pass reroute order while keeping every route in a batch mutable until validation.

Do not claim completion from the 51 passing tests. Completion requires the official candidate to pass V2 and V3 with all three defect categories at zero.
