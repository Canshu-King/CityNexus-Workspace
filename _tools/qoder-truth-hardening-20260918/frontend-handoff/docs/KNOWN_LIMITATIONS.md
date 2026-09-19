# Known limitations — honest scope of what is NOT verified

These statements are deliberate. Green programmatic gates are **not** the same
thing as a human visual sign-off, and this line must not be mistaken for one.

1. **No human visual screenshot review was performed.** The isolated Qoder
   environment cannot write screenshot files that this session is able to read
   back (Playwright image output lands in a sandbox path unreadable from here).
   Therefore all acceptance here is DOM / `getComputedStyle` / `boundingRect`
   based. Colour harmony, visual rhythm, iconography polish and "does it feel
   Apple" are **pending** authoritative integration + a Playwright screenshot
   review with a human (or a readable-image harness).

2. **Pre-existing, environment-bound Live/legacy specs cannot run here.**
   `v10-live-execution`, `live-autopilot-v5`, `golden`, `product-v8`,
   `product-hardening`, `v10-accessibility`, `v10-inbox`,
   `v10-quality-budget`, `real-world-trip-operations-v9`,
   `predictive-real-city-v6`, `v13-5-fully-grounded` navigate to `/v8` or `/`
   expecting a **globally seeded** `citynexus.v8.journey_id` (or a specific
   demo journey / persisted Control-Tower mission) that the fresh isolated
   harness + its reused backend does not provide. Each fails at its very first
   "is the journey there?" assertion. This was confirmed pre-existing (a
   `git stash` of the frontend changes reproduces the identical failure on
   `v10-live-execution`), i.e. **not a regression from this line**. The Qoder
   gates deliberately self-seed (real backend demo button, or a self-contained
   route mock) so they do not depend on that missing global seed.

3. **Full-suite tally for the record:** `npx playwright test` in this harness =
   29 passed / 16 failed, and **all 16 failures are the category (2) above** —
   none are in a `qoder-*` gate. Now captured verbatim in
   `evidence/raw_full_suite.log`, with a per-spec classification in
   `evidence/FULL_SUITE_SUMMARY.txt`. (Per GPT's review this classification must
   still be *re-proven* — i.e. those specs reaching real business assertions — in
   a real-seed integration environment, not argued further in isolation.)

4. **Dark coverage of replan-only surfaces is mocked, not screenshot-verified.**
   L1/L2 dark states are checked with the same 4-tier contrast scan, but the
   exact fill/shadow *aesthetic* of the proposal card is unverified by eye.

5. **No merge.** Nothing here was applied to `D:\moodle\CityNexus` main; the
   truth line (v6) and this frontend line are both isolated. Valhalla, the
   Xiaomi smoke test, and real routing-provider integration remain owner
   actions outside this line.

6. **`typecheck:all` uses `strict: false`.** "typecheck:all clean" therefore
   means zero errors under that broad, non-strict coverage config — it is NOT a
   strict-TypeScript guarantee. Adequate to guard this phase; enabling
   `strict:true` is a deliberate, separate future effort, not silently claimed
   done here.

7. **Large production chunks remain.** `npm run build` is green but still warns:
   `maplibre-gl ≈ 1.05 MB`, `main ≈ 1.13 MB`. This is mobile load/perf debt to
   tackle separately — it is distinct from (and not caused by) the
   transform/opacity motion work, and is not a Pass-1 merge blocker.
