# Deep Track F — Model-based / property-based journey recovery audit

Goal:
Stress the recovery state machine beyond hand-written examples.

Create an isolated harness using Hypothesis / stateful testing or another
deterministic model-based approach.

State model should include:
- journey
- active plan
- disruptions
- ACK
- proposals
- accepted proposal
- activities / places / aliases
- bookings / commitments
- mobility facts and provenance
- budget evidence

Required invariants:
1. ACK alone never resolves the disruption.
2. ACCEPTED proposal only resolves its linked trigger event.
3. Unrelated ACCEPTED proposal cannot close another disruption.
4. A physically closed venue cannot re-enter via alias/re-ID.
5. Ambiguous identity is not treated as definite SAME.
6. Live-provider failure cannot promote mock/frozen facts to hard truth.
7. Hard mobility must satisfy the accepted fact-quality allowlist.
8. An accepted replan must produce a material itinerary change unless explicitly
   classified as no-alternative/protected/clarification.
9. Protected bookings/commitments survive unless the proposal explicitly models
   a valid change.
10. Budget UI cannot claim whole-trip certainty from partial activity evidence.
11. After accept, Today / Live / active-plan identity agree.
12. Repeated retry / ACK / accept sequences remain idempotent.

Generate:
- randomized transition sequences;
- shrunk minimal failing examples;
- replayable JSON cases;
- targeted regression tests for real defects.

Do not modify the authoritative trees. If a real bug is found, produce a small
candidate patch in the isolated Codex output only.
