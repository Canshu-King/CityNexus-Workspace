# Frontend implementation report — Apple-style track, Pass 1–5

Branch `qoder-frontend`, worktree `_qoder_th_20260918`, baseline = the v6 truth
line (`master`). This is **primarily a design-system + information-architecture
pass**, guarded end-to-end by programmatic gates, and it adds no product
*feature*. It is **not a 100% pure-visual patch**: it also contains one
deliberate navigation-behaviour change in the Today hero, a small client-side
Now/Next derivation, and prerequisite type-safety fixes required to make the app
type-checkable at all. Those are listed precisely under
"Not purely visual — the honest exceptions" and in `docs/KNOWN_LIMITATIONS.md`.
Every claim is backed by a log in `evidence/`.

## Design principle applied
Adapted from GPT's brief: a restrained Apple system — system font, Apple grey
palette that flips for dark, one dominant action per screen, hierarchy/whitespace
over decoration, motion only on `transform`/`opacity`, every surface bound to a
token so light and dark stay coherent. Bounded changes driven by measurement,
never bulk find-and-replace.

## 1. Design tokens + motion (`src/design-tokens.css`)
- Palette (light + `prefers-color-scheme: dark`), `--cn-accent-solid` (deep blue
  fill so white button labels clear AA in dark), `--cn-control-border` (a ≥3:1
  boundary reserved for outline-only controls), type scale, spacing, unified
  radii, restrained shadows, motion tokens (`--cn-ease-*`, durations).
- Page-reveal = **one** staggered group, capped; press/hover are transform-only;
  `focus-visible` ring ≥2px; touch targets ≥44px; full `prefers-reduced-motion`
  opt-out.
- Bound to the existing shell by remapping `--v8-*` on `.v8-product-shell`, so no
  component markup had to change to adopt the palette.

## 2. Type safety (prerequisite)
`@types/react` + a real `tsconfig.typecheck.json` gate. Installing the missing
types turned 16 "unexplained" errors into 0 and surfaced **6 genuine** type
errors (one a real golden-scenario `setSession` bug), all fixed. `typecheck:all`
is now a hard gate. (`evidence/raw_typecheck.log`)

## 3. Dark mode — a durable 4-tier gate, then a controlled convergence
`e2e/qoder-dark-audit.spec.ts` (+ shared `_qoderContrastScan.ts`) runs in emulated
dark over the real Today + Live surfaces at mobile and desktop and FAILS on:
- **Text AA** — body < 4.5:1, large < 3:1 (WCAG relative-luminance math, with a
  walk-up background composite, so translucent layers are handled honestly);
- **Light surface** — a control/card painting ~white in dark (un-tokenised);
- **Control boundary** — a `data-contrast-role="control"` that is identifiable
  only by its ring and has neither a ≥3:1 fill nor a ≥3:1 border vs the page;
- **State indicator** — a `data-contrast-role="state"` (selected/active) that
  relies on colour alone with no fill/weight/pill cue;
- **Focus ring** — a real `Tab` focus (`:focus-visible`) needing ≥2px outline and
  ≥3:1 vs its ACTUAL surrounding background.
Decorative borders/separators/shadows are counted as **warnings only** — never
gating, per GPT's "don't turn the audit into border-policing".

Non-vacuous proof (the gate actually catches things): first run reported **32**
text/light-surface violations; after token-migrating exactly the flagged classes
it reached **0**. The control tier first flagged **14** real defects (weakly
bounded language/outline buttons + mis-tagged nav tabs) → fixed with
`--cn-control-border` + correct `state`-only tagging → 0. The Live reorder later
surfaced a hard-coded `#fff` mode-chip fill and an unbounded map — caught and
fixed the same way. (`evidence/raw_dark_audit.log`, `dark-audit-*.json`)

## 4. Today — hierarchy + single Now/Next hero
`e2e/qoder-today-hero.spec.ts` locks GPT's hero acceptance:
- one `.cn-now-next-hero` card (radius 20 / pad 24, one reveal group, no
  per-child stagger), next-row as the display focal, now-place secondary;
- "Now" renders **only** when an activity is genuinely in progress (a pre-trip
  journey degrades to "Next" — never an empty current slot, `data-now=false`);
- exactly one primary CTA, and only when there is a real next stop;
- Stay + arrival/departure demoted to a compact secondary strip;
- Attention promoted to its own band: open → warm card + Live CTA, handled →
  quiet line, clear → near-zero footprint ("无事就闭嘴").
Gate asserts: ≤1 primary CTA, no internal horizontal overflow, hero height
≤45% viewport at 360/412/430/1280, no empty Now block, CTA-iff-actionable, and
reduced-motion suppresses the translate reveal. (`evidence/raw_today_hero.log`)

## 5. Live — A+ state-prioritised information architecture
`e2e/qoder-live-structure.spec.ts` (4 phases):
- **Phase 1 — state matrix**, self-contained mock (its own journey id; varies
  only `/experience` disruptions and `/replans` proposal statuses, never
  production logic): L0 NORMAL / L1 UNRESOLVED / L2 PROPOSAL_READY / L3 ACCEPTED
  / L4 refusal, each locking the right number of Accept CTAs.
- **Phase 2 — DOM order** via bounding rects: current.top < map.top <
  disruption.top < proposal.top; single Accept CTA when a proposal is ready; the
  Copilot dock must not *intersect* the CTA.
- **Phase 3 — accepted transition** with a stateful mock (POST accept flips the
  proposal): a positive confirmation surfaces, and the open warning collapses
  only once handled — asserted as state order, not a millisecond timeout.
- **Phase 4 — dark on the mock states** (L1/L2 through the same 4-tier scan) +
  map height by state (L0 240px, decision 200–216px) + first-screen: at
  412×915 the disruption title and the L2 Accept CTA sit above the fold.
The reorder put the LiveRecovery decision block between the map and the
secondary cards in the **DOM** (not a CSS-order illusion), and removed
LiveRecovery's duplicate "现在的行程" header inside the shell so the screen has a
single current state. The replan accept motion stays presentation-only
(`data-state`, transform/opacity); it never introduces a business "accepting"
state and never participates in `isDisruptionOpen` / `acceptedTriggerIds`.
(`evidence/raw_live_structure.log`)

## Invariants honoured
No data-testid was deleted. No truth/acceptance computation was touched:
`isDisruptionOpen`, `isDisruptionAcknowledgedOnly`, `acceptedTriggerIds`, the
proposal↔`trigger_event` linkage, the API calls, and the data sources are
unchanged. The 12 self-seeded rendered specs (T3 ack-vs-resolution on Today +
Live, T4 budget-evidence) stay green, proving those behavioural contracts
survive the restructure. (`evidence/raw_rendered.log`)

### Not purely visual — the honest exceptions
GPT's independent patch review corrected the earlier blanket "handlers/logic
unchanged" wording. Precisely, this cumulative patch also contains:
1. **A navigation-behaviour change**: the Today hero's primary CTA now calls
   `onNavigate("live")`, where the old hero tile's quiet action went to
   `onNavigate("studio")`. This is a deliberate information-architecture choice
   (the hero's single action is the live journey) and was product-approved, but
   it *is* a behaviour change, not a pure restyle.
2. **A client-side Now/Next derivation**: new `currentStop` / `nextUp` compute
   the real current vs upcoming activity from wall-clock against
   `active_plan.activities`. This is presentation logic, not CSS.
3. **Prerequisite type fixes** to non-visual files so the whole app type-checks:
   `main.tsx` (golden `setSession` spread — a real bug), `v10Execution.ts`,
   `v8Types.ts`, `AgentComposer.tsx`, `PlanComparison.tsx`, `MapPanel.tsx`,
   `PushCapabilityCard.tsx`, `SortableActivityList.tsx`, and the V12 story.
4. **An inert `data-state` attribute** on the LiveRecovery proposal card —
   presentation only; it never feeds any truth/acceptance decision.

### Integration guidance (GPT)
Do not blanket-apply `frontend-pass1-5.patch`. Split at merge time into
**A — Apple visual/IA** (`design-tokens.css`, V8Experience hero/attention/live
sections, LiveRecovery `data-state`, the new tests) and **B — prerequisite
type/behaviour fixes** (main.tsx, v10Execution.ts, v8Types.ts, AgentComposer,
etc.). If the authoritative branch already has newer versions of the B files,
keep the authoritative code and port only what is genuinely missing — never
downgrade main to make the patch apply cleanly. Both this line and the v6 truth
line edit `V8Experience.tsx` and `LiveRecovery.tsx`, so a real-seed
`truth-integrated` commit must land first and this branch rebased onto it.

## Mobile-overflow gate
`e2e/qoder-mobile-overflow.spec.ts`: no horizontal overflow on Today/Live at
360/412/430. (`evidence/raw_overflow.log`)

## Verdict — assigned by GPT after independent review
GPT unpacked and cross-checked the package himself (verified SHA-256, zip
integrity, the 20-file / +1989 / -201 patch scope, and the logs) and issued:
**FRONTEND_APPLE_PASS1_PROGRAMMATICALLY_READY_FOR_VISUAL_INTEGRATION**
— programmatic phase accepted; the human visual phase has *not* happened yet.
The branch is now `FROZEN FOR REVIEW`: no Trips / Copilot / Onboarding / Me /
Hotel / Bookings work, and no opportunistic cleanup of remaining V8 history.
The next step (real-seed environment + Playwright screenshots + Xiaomi 13 Ultra
on-device) will yield `..._VISUALLY_ACCEPTED_FOR_MERGE` or
`..._VISUAL_INTEGRATION_BLOCKED`. See `docs/KNOWN_LIMITATIONS.md` (what is not
verified) and `docs/NEXT_INTEGRATION_GATE.md` (what to do next).
