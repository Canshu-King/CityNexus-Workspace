# CityNexus V14 Trial Readiness

Date: 2026-09-14 (Asia/Shanghai)

## Outcome

The narrow V14 trial-readiness pass is complete in `D:\moodle\CityNexus`. The existing V14 recovery, Guardian, solver, Agent Gateway, PlanVersion, JourneyTwin, provider-grounding, and offline architecture was preserved.

The Road-Prep archive did not contain the exact filename `CODEX_V14_TASK_PROMPT.md`; it contained `CODEX_V14_TRIAL_TASK_PROMPT.md`. That present trial prompt was used as the package specification, together with the user's explicit V14 scope.

## Product changes

- First boot opens an explicit Journey setup instead of silently creating Tianjin.
- The setup accepts city, country/region, timezone, dates, arrival/departure locations, party size, and budgets.
- Datetime-local inputs are converted using the selected IANA timezone before the Journey is sent to the server.
- Tianjin sealed replay is available only through a clearly labelled demo action.
- `Try another city / 试用其他城市` returns to setup without localStorage editing.
- Generic-city discovery defaults to live providers and visibly reports unavailable live data.
- Tianjin replay cannot be injected into a non-Tianjin Journey, including backend direct calls.
- Live anchor lookup uses the human arrival location and city label when no server-owned coordinate exists.
- Sourced evidence queries no longer contain a hard-coded Tianjin literal.
- Stay query defaults are city-neutral.
- The existing LocaleContext powers the prominent setup/home switch, persists the selection, and synchronizes `html[lang]`.

## Verified outcome

- First boot: no automatic Tianjin Journey.
- Chinese switch: `localStorage[citynexus.locale] = zh-CN` and `document.documentElement.lang = zh-CN`.
- Tianjin sealed demo: opens City Discovery with sealed replay selected.
- Fuzhou trial: created through the UI, opened City Discovery with `实时供应商` selected.
- Fuzhou live discovery: provider-unavailable result was visible; no Tianjin candidates were shown.
- Returning to setup: `试用其他城市` was exercised from the Journey Hub.

## Runtime status

- Frontend: `http://127.0.0.1:5173/v8/hub`
- Backend: `127.0.0.1:8000`
- Generic live-city flag: enabled for the launched backend process.
- DeepSeek key: not configured in this Windows profile for this run; deterministic semantic fallback is active.
- Live Valhalla URL: not configured; no live traffic claim is made.
- Tianjin sealed V14 recovery remains the reproducible grounded recovery demonstration. Generic-city operation depends on live Nominatim/Overpass and any configured mobility provider; unavailable providers are labelled rather than replaced with Tianjin evidence.

## Evidence

- Focused trial/V14 regression: `4 passed`.
- Broad backend convergence: `392 passed, 2 skipped, 2 warnings`.
- Final frontend production build: green, Vite transformed 1,900 modules.
- Playwright session `v14trial`: first boot, locale switch, Tianjin demo, switch-city setup, Fuzhou create, live discovery failure path.
- Browser screenshot: [v14-trial-fuzhou-live.png](./v14-trial-fuzhou-live.png).
- Target artifact: `CityNexus-V14-Grounded-Adaptive-Journey-Recovery-20260913.zip`.

