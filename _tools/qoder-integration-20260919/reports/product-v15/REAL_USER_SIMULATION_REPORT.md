# ey to verify the honest deterministic
fallback path.

## Scenarios exercised

| Scenario | User journey | Observed result | Product decision |
|---|---|---|---|
| Tonglu, low budget | Two travelers, CNY 300 total / CNY 120 stay, late 11:00 start, quiet indoor places, low walkingV15 Real-User Simulation and Product Hardening

## Scope and runtime honesty

This is a browser-led acceptance pass against the live V8/V15 frontend at
`http://127.0.0.1:5173`, with the backend bound to the authoritative
`D:\moodle\CityNexus\citynexus.db`. The pass used Playwright through the
user-facing setup, City Discovery, Stay Explorer, Journey Hub, and AI desk.

The requested eight-hour wall-clock budget was not consumed. The measured
Codex goal window at report time was 43 minutes 41 seconds. This report records
the actual engineering window rather than inventing a longer duration.

During the first live-provider portion, the user-supplied DeepSeek key was
loaded only into the backend process environment. It is absent from source,
reports, screenshots, staging, and release artifacts. The final verification
server was restarted without the k | Journey creation and Copilot preference interpretation worked; no unsupported plan was fabricated when provider evidence was insufficient | Keep the journey unchanged until grounded evidence exists |
| Xiapu, small county | Two travelers, CNY 100 total / CNY 50 stay, 12:00 start; rain and traffic interruptions | Live discovery returned no feasible grounded place set; the UI explained that outcome. A hypothetical rain question remained read-only; a current disruption created a user-reported Event and opened recovery review | Preserve generic-city truth isolation and distinguish “what if” from “happening now” |
| Tianjin, sealed replay | Two travelers, captured stay selected, multi-day plan, then “What if I stay 60 minutes longer?” | What-If rendered `CN¥480`, 34 minutes walking, `PASS`, `SIMULATION ONLY`, and preserved protected commitments. The Chinese late-start/no-morning request reached replan review | Read-only simulation is useful only after an authoritative PlanVersion is selected |
| Beijing, high budget | Two travelers, CNY 20,000 total / CNY 10,000 stay, Beijing South → Capital Airport, 11:00 start and 20:00 end | Creation preserved the requested late-start schedule. Live discovery failed at the external DeepSeek/provider boundary and the UI reported that honestly; no Tianjin data leaked into Beijing | External provider failure is visible, not converted into invented candidates |

## Concrete fixes made from the simulation

1. DeepSeek Responses reasoning items are retained for continuation but are no
   longer concatenated into the structured JSON text. The actual response
   envelope observed in the live probe contained a reasoning chain followed by
   the final schema message; the old parser tried to `json.loads` both.
2. Explicit schedule edits such as “第二天十一点才起床，上午不要排活动” now
   route to `REPLAN_REQUEST`, even when DeepSeek softens them into a
   preference. The model still supplies the explanation/badge, but cannot
   downgrade a direct plan edit into a soft-only action.
3. What-If activity selection skips locked arrival/commitment anchors and uses
   the first flexible activity when the user does not name a title.
4. Copilot cost metrics now display currency amounts (for example `CN¥480`)
   rather than raw minor units.
5. New journeys now default to a human schedule (10:00 next day to 20:00 on
   day three) instead of the previously observed 02:00–02:00 window.
6. Provider/DeepSeek discovery failures and no-grounded-candidate results have
   user-facing localized explanations. They do not mutate the selected plan.
7. When the user tries What-If before selecting an authoritative PlanVersion,
   the response now explicitly says to choose a provider-backed plan in Stay
   Explorer; it no longer looks like a silent blank simulation.

## Safety and authority observations

- Hypothetical weather, closure, and budget questions did not create Events,
  bookings, payments, JourneyTwin writes, or PlanVersion mutations.
- A current disruption report did create a `USER_REPORTED` Event through the
  server route and offered recovery review.
- Coordinates, prices, route times, opening hours, and committed state stayed
  server/provider-owned; DeepSeek was used for semantic interpretation.
- A generic city never borrowed Tianjin sealed replay facts.

## Remaining product limits

- Live discovery can legitimately return no grounded candidate set, or a
  provider can fail. The product now exposes that state, but it cannot create a
  fully grounded plan without evidence.
- A generated candidate option is not an authoritative PlanVersion until the
  traveler selects it in Stay Explorer. This is now explained directly in the
  What-If response.
- The live DeepSeek discovery path was intermittently unavailable during the
  run; the structured Copilot path and deterministic fallback remained usable.

## Evidence

- `output/playwright/v15-fuzhou-copilot.png`
- `output/playwright/v15-tianjin-copilot-what-if.png`
- `output/playwright/v15-real-user-no-plan-guidance.png`
- `tests/test_v15_copilot.py`
- `tests/test_v10_foundations.py`
