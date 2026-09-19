# Next integration gate — what to do once there is a real seed + readable screenshots

Ordered so a reviewer can confirm the programmatic baseline visually, then push
past what this line could not.

## 0. Prereq: a seeded environment this line lacked
Provide a browser context / backend where `citynexus.v8.journey_id` points at a
journey with a **chosen active plan** (located activities + legs) and, ideally, a
persisted disruption + a PRESENTED replan proposal. With that seed, the 16
currently-blocked legacy specs (`v10-*`, `golden`, `product-v8`,
`product-hardening`, …) should run and pass — that is the first regression net
this line could not use.

## 1. Visual review with screenshots (the missing sense)
Run a Playwright screenshot pass over Today and Live in **light + dark**, at
360 / 412 / 430 and a desktop width, and eyeball:
- token palette, card material, radius/spacing rhythm;
- the single Now/Next hero focal;
- Attention states (open / handled / clear) read at a glance;
- Live A+ order: Current → Map → Disruption/Replan → secondary;
- the proposal card + accepted motion settle.
Fix anything the computed gates cannot see (optical balance, icon weight, map
legibility behind the honest-empty state).

## 2. Items intentionally left on the table (this line stopped at the gates)
- **Positive Hero branch with a real next stop.** The Today-hero gate asserts the
  empty/no-plan branch (pre-trip demo) + the "≤1 CTA / no empty slot" invariant;
  the "real next stop → exactly one CTA" positive path needs the seeded plan
  above to exercise in the product (it is asserted by the bidirectional rule but
  only the empty branch fires on the demo).
- **Live L4 true `MOBILITY_DATA_UNAVAILABLE`.** Phase-1 models it as a rejected
  proposal (safe fallback, no fake CTA). The real engine refusal (T2 truth
  contract) should be reproduced end-to-end once Valhalla/routing is wired.
- **Copilot minimisation to a pill during a decision.** The gate now only
  asserts the Copilot dock never *intersects* the Accept CTA; the deliberate
  "collapse to pill while a replan decision is on screen" polish is not done.
- **Full dark tokenisation of secondary/history surfaces** beyond Today/Live
  (Trips, Studio, Bookings, Me, Control Tower) — GPT scoped this pass to
  Today/Live reachable surfaces; the rest is declared debt.

## 3. Merge decision
If visual review + the seeded legacy specs pass, this line's verdict upgrades
from `...PROGRAMMATICALLY_READY_FOR_VISUAL_INTEGRATION` to a merge candidate.
Merging, freezing the main-repo baseline, and the truth-line integration
(Valhalla, Xiamen smoke, Xiaomi 13 Ultra) are **owner** actions, not this line.
