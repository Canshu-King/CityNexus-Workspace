# CityNexus Vertical Slice Hardening Checkpoint

Date: 2026-09-10

This checkpoint records the current CityNexus worktree after the supplied
Vertical Slice Hardening contract was applied and its deterministic gates were
run. It is prepared for independent GPT review.

## Scope completed

- Added the two supplied adversarial hardening tests.
- Normalized aware and naive Event timestamps into the Journey schedule
  timezone before deterministic replan evaluation.
- Made F3 use the authoritative `Journey.current_activity_id` as its origin,
  with the disrupted slot's previous activity retained only as fallback.
- Added `origin_key` to F3 opportunity-window evidence.
- Advanced the backend Golden Scenario through the prefix to Tech Art before
  the 13:25 closure.
- Connected the frontend Golden Scenario to the same execution prefix,
  corrected monetary minor-unit display, and scoped CAPTURE, generation, and
  acceptance idempotency keys to their domain objects.
- Passed closure occurrence time into the JourneyTwin refresh and added the
  browser assertions for Tech Art, the ¥130 remaining budget, F3 origin, and
  the +08:00 window opening.
- Included the source SQL schema and backend-relative deterministic fixtures in
  the checkpoint so a fresh extraction does not depend on an old archive or a
  generated database.

## Authority and boundaries

The uploaded assist package is retained under
`contract/vertical-slice-hardening/`. Its patch files were semantically merged
against the newer current tree; they were not applied blindly. Existing
Domain, Requirements, and Visio baselines were not edited. No rollback,
reset, clean, or automatic commit was performed. Hash computation and hash
verification were skipped as directed.

The default path remains offline and mock-first. Live Valhalla, OR-Tools,
LiteLLM/DeepSeek, live payments, and external Providers remain optional and
were not expanded in this checkpoint.

## Stop point

The required hardening gates are green. Work stops here for external GPT
validation; no subsequent provider-runtime or WP05 work is included.
