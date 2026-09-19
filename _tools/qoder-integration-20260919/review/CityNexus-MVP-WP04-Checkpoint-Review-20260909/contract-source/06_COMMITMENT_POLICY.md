# Commitment Policy — WP04 to WP06 bridge

## Source constraints

The real requirements establish:

- FR-029: confirmed source events create or strengthen Commitment, and payment alone must not decide strength.
- FR-030: exactly five source strength levels exist.
- BR-011: strength derives from multiple factors; a fixed unpaid commitment may be stronger than a low-impact paid one.
- BG-004 / BR-009: C4/Anchored must be preserved during normal replanning.
- BR-010: material C2/C3 changes require explicit traveler confirmation.

## Consequence

Do not model strength as the four labels `FLEXIBLE/RESERVED/PAID/LOCKED` long-term. In particular, `PAID` is a payment fact, not a sufficient strength definition.

## Required local reconciliation

Before WP04 schema/API commit, Codex reads the frozen YAML and records the **exact five** `commitment_strength` enum values and their order. This is the only source read needed; do not re-research the domain.

Use a map:

```python
SOURCE_STRENGTHS = [exact_C0, exact_C1, exact_C2, exact_C3, exact_C4]
rank(code) -> 0..4
code(rank) -> exact source code
```

## Deterministic derivation inputs

Strength may consider:

- provider-confirmed reservation;
- payment/capture outcome;
- fixed scheduled time;
- explicit traveler lock/must-go flag;
- cancellation/rebooking loss;
- provider cancellation policy;
- replaceability/flexibility.

For MVP, use the bounded reference rank policy from `reference_patch/backend/app/commerce/commitment_policy.py`.

## Canonical River Cruise

Facts:

- Activity is fixed at 15:30;
- selected plan marks it locked/must-go;
- Booking provider confirms;
- Payment CAPTURE succeeds;
- changing/removing it has material schedule/financial impact.

Expected result:

```text
Commitment status = ACTIVE
strength rank = 4
strength code = exact source C4 Anchored code
semantic_key = place-river-cruise
scheduled_start_at = 2026-10-10T15:30:00+08:00
```

This becomes WP06's hard preservation input.

## Negative proof

A successful payment for a flexible, easily refundable/unfixed item must **not** automatically become rank 4. Add a test. This is the easiest way to prove BR-011 was not reduced to `if paid: LOCKED`.

## Stronger deterministic C4 guard used by the reference code

The supplied policy deliberately requires the canonical C4 decision to have all of:

- provider-confirmed source;
- captured payment;
- fixed schedule or explicit traveler lock;
- not easily replaceable.

This keeps the pre-payment canonical booking at rank 3 and makes the successful capture the final multi-factor evidence that reaches rank 4. A paid but low-impact/easily-replaceable item remains below a fixed unpaid commitment, which directly exercises BR-011 rather than merely asserting it in prose.
