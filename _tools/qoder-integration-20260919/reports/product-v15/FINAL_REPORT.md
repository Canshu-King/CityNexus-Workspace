# CityNexus V15 Conversational Copilot + What-If Studio

## Outcome

V15 is implemented against the authoritative `D:\moodle\CityNexus` worktree. The user-facing AI desk now calls the explicit Copilot contract instead of the legacy free-text Agent command route. Ordinary preference, explanation, discovery, replan, and hypothetical requests no longer become fabricated WEATHER events.

The release preserves the V14 recovery, PlanVersion, JourneyTwin, Commitment, provider-evidence, and generic-city isolation paths. A real current disruption reported through Copilot is captured as a server-scoped `USER_REPORTED` Event; a hypothetical disruption remains a read-only simulation. A browser-led real-user pass across low-budget, small-county, sealed-replay, and high-budget city journeys added narrow hardening for late-start schedule edits, no-plan What-If guidance, reasoning-envelope parsing, currency display, flexible activity targeting, and sane setup defaults.

## Implemented surface

- Seven explicit intents: `EXPLAIN_PLAN`, `WHAT_IF`, `DISCOVER`, `PREFERENCE_CHANGE`, `DISRUPTION_REPORT`, `REPLAN_REQUEST`, and `UNKNOWN`.
- DeepSeek Responses structured JSON interpretation when a configured key is available, with deterministic fallback and an honest `FALLBACK` badge when it is not.
- Verified server context containing city, timezone, selected PlanVersion facts, current Activity, commitments, preferences, and mobility evidence. Model output cannot authoritatively supply IDs, coordinates, prices, provider facts, or mutations.
- Read-only What-If previews for activity extension, budget/cost and walking preferences, indoor alternatives, and hypothetical weather/closure. Results expose before/after values, deltas, feasibility, affected Activities, commitment preservation, provenance, and an explicit next action.
- No What-If write to PlanVersion selection, JourneyTwin, Commitment, Booking, Order, or Payment tables.
- Bilingual Copilot history, intent/provider badges, simulation-only card, protected-commitment summary, explicit replan/discovery/preference navigation, and suggested prompts.
- OpenAPI and generated frontend contract updates.

## Validation

- Focused baseline: 9 passed.
- Final focused suite: 12 passed (`test_v15_copilot.py` + `test_v10_foundations.py`).
- V15 plus V14 recovery reference suite: 7 passed.
- Broad backend `uv run pytest -q`: `400 passed, 2 skipped, 2 warnings` in 39.62 seconds.
- Frontend production build: passed with Vite; only the existing large-chunk warning remained.
- Browser: Fuzhou generic-city Copilot flow and sealed Tianjin What-If flow passed. The final Tianjin flow showed before/after selected-plan metrics, `SIMULATION ONLY`, `BLOCKED` feasibility for a locked current Activity, and zero console errors.

## Honest runtime labels

The initial live-provider browser window loaded the user-supplied DeepSeek key
only into the process environment. DeepSeek AI badges were observed on Copilot
interpretations for the Tianjin/Xiapu flows, and a live Responses probe exposed
the reasoning-plus-final-message envelope that prompted the parser fix. Some
discovery calls still failed at the external provider boundary and were shown
as unavailable. The final verification window deliberately ran without a key
and confirmed the honest deterministic fallback badge. No API key is stored in
the repository or release artifact.

This was an implementation pass within the available interactive engineering
window, not a claim that an eight-hour wall-clock budget was consumed. The
measured Codex goal window at finalization was 43 minutes 41 seconds.

## Known limits carried forward

- Provider-dependent alternative cost, walking, indoor, and hypothetical weather claims return `NEEDS_LIVE_EVIDENCE` until a real or sealed provider capture exists.
- A generic Journey with no selected PlanVersion returns `NOT_SIMULATABLE_FROM_CURRENT_EVIDENCE`; it does not borrow Tianjin facts.
- Newly generated candidate options remain non-authoritative until a traveler
  selects one in Stay Explorer; the Copilot now explains this boundary instead
  of presenting blank What-If metrics without context.
- The legacy `/agent/commands` endpoint remains for existing V14 clients. The current Agent UI no longer calls it; all ordinary Copilot text uses `/copilot/messages`.
- The DeepSeek live structured-output branch is implemented and contract-tested at the boundary, but no live provider call was claimed without a configured key.

## Evidence

- [COPILOT_INTENT_CONTRACT.md](COPILOT_INTENT_CONTRACT.md)
- [WHAT_IF_EVIDENCE.md](WHAT_IF_EVIDENCE.md)
- [GATE_MATRIX.md](GATE_MATRIX.md)
- [TEST_RESULTS.md](TEST_RESULTS.md)
- [TRIAL_INSTRUCTIONS_ZH.md](TRIAL_INSTRUCTIONS_ZH.md)
- UI captures: `output/playwright/v15-fuzhou-copilot.png` and `output/playwright/v15-tianjin-copilot-what-if.png`
- [REAL_USER_SIMULATION_REPORT.md](REAL_USER_SIMULATION_REPORT.md)
- UI capture: `output/playwright/v15-real-user-no-plan-guidance.png`

The final release archive was extracted into a fresh directory and its backend
tests ran there: `12 passed, 2 warnings`. The release staging pass initially
found that `data/mock` was required by `/demo/reset`; the final archive includes
those non-secret fixtures.
