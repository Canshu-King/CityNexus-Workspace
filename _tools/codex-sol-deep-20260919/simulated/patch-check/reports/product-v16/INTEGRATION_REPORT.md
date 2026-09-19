# CityNexus V16.1 Real-User Hardening Integration Report

Date: 2026-09-14 (Asia/Shanghai)

Worktree: `D:\moodle\CityNexus`

Release target: `CityNexus-V16.1-RealUser-Correctness-20260914.zip`

## Result

The WorkBuddy V16 findings were integrated selectively into the current V15
Copilot architecture. `patches/v16_production.patch` was not applied: it
targets the older semantic-router tree and does not match the authoritative
V15 `/copilot/messages` path.

The V16.1 closure validation is green: **409 passed, 2 skipped** in the final
backend regression, and **20 passed** in the final focused V16/V15/V14 set.
The V16.1 focused closure itself is **9 passed**. The frontend production build is
green. Two fresh real-user browser paths were exercised against a restarted
backend running the current worktree.

No DeepSeek key was written to the repository, process configuration, report,
or release package. The browser run used the deterministic fallback because no
live key was configured in the running process; all responses were visibly
labelled as deterministic fallback rather than being presented as model-backed.

This report does not claim an artificial eight-hour elapsed duration. It records
the actual implementation and validation performed in this session.

## Implemented slice

### Semantic event boundary

The current V15 Copilot decision boundary now distinguishes current reports
from non-events before any Event mutation:

| User statement | Result |
| --- | --- |
| `现在博物馆关门了` | `DISRUPTION_REPORT / CLOSURE` |
| `火车晚点三个小时` | `DISRUPTION_REPORT / SCHEDULE_DELAY` |
| `前面正在封路` | `DISRUPTION_REPORT / TRAFFIC_DELAY` |
| `现在下暴雨` | `DISRUPTION_REPORT / WEATHER` |
| `如果明天下雨会怎样？` | no city Event; `WHAT_IF` |
| `我以前遇到堵车了，类似情况怎么办？` | no city Event |
| `朋友说五大道关闭了，真的假的？` | no city Event |
| `现在路很顺畅，没有堵车` | no city Event |
| `我护照丢了` | no city Event; personal-emergency language |
| `我想少走路` | no city Event; preference |

Closure vocabulary includes closed/not-open, maintenance, construction,
temporarily unavailable, power outage, and water outage forms in Chinese and
English. The Chinese character `了` is not used as evidence of current reality.
The legacy `/agent/commands` endpoint now uses the same deterministic boundary
and no longer creates a hard-coded WEATHER event for every command.

Future-known disruptions are separated from hypothetical or unverified future
language: `明天的航班已经取消了`, `明天火车晚点三个小时`, and
`后天景区通知闭馆` are `ASSERTED/FUTURE` and eligible for recovery, while
`明天可能下雨`, `明天会不会堵车`, and `明天航班没有取消` remain non-events.
The same distinction is covered for confirmed/cancelled English reports.

### Traveler rhythm

`backend/app/planning/day_rhythm.py` provides a small shared representation for
wake time, bed time, skipped breakfast, brunch, and late-night preference.
Copilot and mission compilation can supply it as a soft preference. The
authoritative planner applies it only to optional activities and overnight
blocks. ARRIVAL, DEPARTURE, C3/C4, locked activities, and paid/reserved
activities remain protected and are not silently moved.

### Currency semantics

`backend/app/core/money.py` is the shared backend minor-unit rule and
`frontend/src/lib/money.ts` is the shared frontend rule. JPY, KRW, VND, and IDR
use zero decimal places; CNY and other currencies retain their normal minor
unit conversion. Journey creation, budget handling, stay/mobility facts,
What-If parsing, and UI formatting use the same semantics. The old scattered
formatting paths were routed through the shared helper.

### Occupancy

Journey creation now suggests room counts based on party size and records the
source as `SUGGESTED`; an explicit user room count is preserved and recorded as
`USER`. This is a product suggestion, not a universal hotel rule. The setup UI
allows the user to override it.

### JourneyTwin cache writes

The Twin projection remains transactionally computed. Only the narrow SQLite
`database is locked` / `database is busy` cache-write case is treated as
best-effort; the valid read projection is still returned. Other database
errors continue to surface. No catch-all exception layer was added.

## Findings intentionally not merged

- F4 generic synthetic city templates were not merged. V15 generic-city truth
  isolation remains authoritative: a city without captured provider evidence
  cannot silently become a grounded plan.
- F6 was checked once: empty Copilot input is rejected by the backend and the
  current UI disables submission for an empty message; no duplicate gate was
  added.
- F9 was checked once against the current V15 path and is not reachable there;
  no obsolete WorkBuddy module was introduced.
- F10 remains governed by the current V15 `LocaleContext`; it was not regressed.

## Automated validation

- `backend/tests/test_v16_integration.py`: **9 passed, 2 warnings** for the
  final V16.1 semantic and correctness closure.
- Focused V16 + V15 Copilot + Agent mission + V8 Stay/Mobility + V14 recovery
  and trial-readiness tests: **20 passed, 2 warnings**.
- Full `backend/tests`: **409 passed, 2 skipped, 2 warnings**.
- One full-regression compatibility issue was found and fixed during
  convergence: a legacy minimal Journey test did not expose `budget_currency`;
  mission compilation now uses its explicit CNY compatibility default.
- Frontend `npm run build`: **passed** with Vite 7.3.6 (1,901 modules). The
  existing chunk-size advisory remains non-blocking.

## Real-user browser evidence

The final browser exercise was run after restarting the backend from the
current worktree. Generic cities remained in live-provider mode and did not
use the Tianjin replay.

### A — Fuzhou / CNY / late-riser couple

- Created Fuzhou, CN, Asia/Shanghai, 20–22 September, railway-station arrival,
  airport departure, two travelers, CNY 3,000 total budget, one room, CNY 1,500
  stay budget.
- Journey Hub displayed `CN¥1,500.00` and the correct anchors.
- Copilot message “We stay up late, sleep in until 11, skip breakfast, and
  prefer brunch.” routed to **Preference change**, with no silent Twin or plan
  mutation.
- “What if I stay 60 minutes longer?” routed to **What-if** and displayed
  **SIMULATION ONLY**. With no selected provider-backed PlanVersion, the UI
  correctly returned `UNKNOWN` feasibility and stated that nothing changed.

### B — Tokyo / JPY / business traveler

- Created Tokyo, JP, Asia/Tokyo, 25–27 September, Tokyo Station arrival,
  Haneda departure, one traveler, JPY 150,000 total budget, one room, JPY
  60,000 stay budget.
- Journey Hub displayed `¥60,000`, confirming zero-decimal JPY formatting rather
  than `¥60,000.00`.
- “I am on a business trip: keep walking minimal and leave a quiet buffer
  before my meetings.” routed to **Preference change** after the focused fix;
  it did not create a disruption Event.
- “What if I spend 5000 yen on a taxi and walk less?” routed to **What-if**,
  displayed **SIMULATION ONLY**, and preserved the no-selected-plan boundary.
  The UI did not invent a cost delta without a provider-backed selected plan.

## Release hygiene

The release package is built from an allowlisted staging set. The package
excludes repository metadata, virtual environments, node modules, frontend
build output, databases and SQLite sidecars, caches, temporary Playwright
output, environment/key files, and nested archives. The fresh extraction gate
is run against the packaged files, using the backend runtime tests rather than
only checking file counts. The final fresh extraction gate completed with
**20 passed, 2 warnings, exit 0** from:

`test_v16_integration.py`, `test_v15_copilot.py`,
`test_agent_mission_runtime.py`, `test_v8_stay_mobility.py`,
`test_v14_grounded_adaptive_recovery.py`, and `test_v14_trial_readiness.py`.

## V16.1 correctness closure

- `DayRhythm.overnight_minutes` now returns bedtime-to-next-wake duration;
  focused coverage asserts both boundaries for 01:30→11:00, 23:30→07:30,
  and 00:30→08:00, while protected anchors remain unchanged.
- A shared deterministic semantic status boundary rejects negated reports such
  as “the museum is not closed”, “the train is not delayed”, and “the road has
  reopened”, while retaining current closure, delay, cancellation, road,
  and weather events.
- Synthetic mobility uses an explicit CNY-only estimate profile. WALK remains
  free; CNY fixture BICYCLE/TRANSIT/AUTO costs are `ESTIMATED` with
  `CITYNEXUS_ESTIMATE` evidence; non-CNY synthetic paid costs are UNKNOWN with
  no currency or fabricated amount. The captured accommodation fixture is
  explicitly labelled CNY-only.
- Final focused closure: **9 passed**. Existing V16/V15/V14 focused set:
  **20 passed**. Final broad backend regression: **409 passed, 2 skipped**.
- DeepSeek live canary was skipped because no key was configured in the process.
