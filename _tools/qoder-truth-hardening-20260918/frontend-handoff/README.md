# CityNexus — Frontend Apple-Style Track · Pass 1–5 handoff

Isolated implementation line (`Qoder`), branch `qoder-frontend` in the
worktree `_qoder_th_20260918`. This package is **programmatic-quality**: the
structure, responsive behaviour, dark-mode, accessibility, and state logic are
held by automated Playwright/computed gates — **not** by a human screenshot
review (see `docs/KNOWN_LIMITATIONS.md`).

Verdict — **assigned by GPT after independent review** (he verified the zip
SHA-256 + integrity + patch scope; branch now `FROZEN FOR REVIEW`):
`FRONTEND_APPLE_PASS1_PROGRAMMATICALLY_READY_FOR_VISUAL_INTEGRATION`
— i.e. ready to enter an integration pass with a real seed environment and
readable screenshots. It is **not** "proven to look like Apple by eye".

Honest scope note: this is a **primarily visual / information-architecture**
patch, but the cumulative diff is **not 100% pure-visual** — it also contains a
deliberate Today-hero navigation-behaviour change (the hero's single CTA now
goes to Live) and prerequisite type-safety fixes. See
`FRONTEND_IMPLEMENTATION_REPORT.md` → "Not purely visual — the honest
exceptions" and the A/B integration split in `docs/`.

## What changed (high level)
- **Design tokens + motion layer** (`src/design-tokens.css`): Apple palette
  (light/dark), system font stack, unified radii/spacing/type scale, motion
  tokens (transform/opacity only, reduced-motion aware), a page-reveal group,
  and theme-token bindings for the existing V8 shell. Additive; no DOM/testid
  edits by themselves.
- **Type-safety prerequisite**: restored React typechecking (`@types/react`)
  and cleared 6 real type errors (incl. a genuine golden-scenario bug), added
  `typecheck:all`. Without this the app could not be type-checked at all.
- **Dark-mode**: a durable 4-tier contrast gate (`e2e/qoder-dark-audit.spec.ts`)
  and a controlled, audit-driven migration of exactly the reachable Today/Live
  surfaces (not a blind colour rewrite). Intent declared in the DOM via
  `data-contrast-role`.
- **Today**: Header → single Now/Next Hero → Attention band (three-state,
  "nothing to report" is near-zero footprint) → Timeline, with an acceptance
  gate (`e2e/qoder-today-hero.spec.ts`).
- **Live (A+)**: DOM reading order restructured to
  Current → Map → Disruption/Replan → downshifted secondary cards, state-aware
  compact map, presentation-only accept motion, and a state-coverage +
  structure + first-screen gate (`e2e/qoder-live-structure.spec.ts`).

## Invariants honoured throughout
No data-testid was deleted, and the truth/acceptance computation
(`isDisruptionOpen`, `isDisruptionAcknowledgedOnly`, `acceptedTriggerIds`,
proposal↔trigger_event, API/data sources) was **not** changed. Wrappers, section
order, classNames, grouping, spacing, heading hierarchy, data-attributes and
presentation-only motion moved. The patch is not pure-visual, though: it also
carries one deliberate Today-hero navigation-behaviour change (single CTA now →
Live), the client-side Now/Next derivation, and prerequisite type fixes — see the
report's "Not purely visual — the honest exceptions".

## Gates (all green — see `evidence/`)
build · typecheck:all · dark audit (4 tiers × mobile/desktop + 2 mock states) ·
mobile-overflow (360/412/430) · Today-hero acceptance · Live-structure
(state matrix / DOM order / CTA / Copilot / map-height / first-screen /
accepted-transition) · 12 self-seeded rendered (ack-vs-resolution + budget
evidence) specs.

## Contents
```
README.md                          (this file)
FRONTEND_IMPLEMENTATION_REPORT.md  (detailed, per commit/gate)
CHANGED_FILES.txt                  (20 files)
COMMITS.txt                        (18 commits, oldest-relevant last)
patch/frontend-pass1-5.patch       (git diff master..qoder-frontend -- frontend/)
tests/                             (the 4 new gates + 2 shared helpers)
evidence/raw_*.log                 (build, typecheck, and each gate run)
docs/KNOWN_LIMITATIONS.md          (what is NOT verified)
docs/NEXT_INTEGRATION_GATE.md      (what to do with real seed + screenshots)
```

## Apply
From a checkout of the same baseline, apply `patch/frontend-pass1-5.patch`
under `frontend/`, then run `npm run typecheck:all`, `npm run build`, and
`npx playwright test e2e/qoder-*.spec.ts` (needs the local backend/preview
servers per `playwright.config.ts`).
