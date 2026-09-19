# Xiaomi 13 Ultra evidence record

## Identity

- Tester:
- Date/time/timezone:
- Device / Android or HyperOS / browser:
- Display and font scale / refresh rate / battery mode:
- Release branch / full commit:
- Artifact SHA-256:
- Backend/frontend URLs (sanitized):
- Valhalla deployment/version/map-data timestamp (no credentials):

## Preflight

| Check | Result | Evidence |
| --- | --- | --- |
| Fresh PWA/service worker state | NOT_RUN | |
| HTTPS and phone reachability | NOT_RUN | |
| Backend health | NOT_RUN | |
| Frontend build identity | NOT_RUN | |
| Location permission paths | NOT_RUN | |

## Chain evidence

| Step | Journey/run/plan/proposal ID | Expected | Actual | Result | Evidence file |
| --- | --- | --- | --- | --- | --- |
| Create | | New Xiamen Journey | | NOT_RUN | |
| Plan | | Real places and versioned plan | | NOT_RUN | |
| Select | | One active plan | | NOT_RUN | |
| Hotel | | Stay identity preserved | | NOT_RUN | |
| Booking | | Simulated reservation protected | | NOT_RUN | |
| Copilot | | Explain before mutation | | NOT_RUN | |
| Map | | Provider route and honest error states | | NOT_RUN | |
| Live | | Current/next and provenance | | NOT_RUN | |
| Disruption | | Trigger linked once | | NOT_RUN | |
| Replan | | Material, live-backed candidate | | NOT_RUN | |
| Accept | | One idempotent transition | | NOT_RUN | |
| Today/Trips/Live | | Same active truth | | NOT_RUN | |

## Provenance sample

```json
{
  "provider": "",
  "fact_quality": "",
  "captured_at": "",
  "time_basis": "",
  "origin": "",
  "destination": "",
  "duration_min": null
}
```

## Faults and recovery

| Fault | User-visible behavior | Fabricated truth? | Recovery | Result |
| --- | --- | --- | --- | --- |
| One route leg fails | | | | NOT_RUN |
| All route candidates fail | | | | NOT_RUN |
| Location denied | | | | NOT_RUN |
| Network/SSE interrupted | | | | NOT_RUN |
| Duplicate Accept | | | | NOT_RUN |
| PWA killed/reopened | | | | NOT_RUN |

## Visual/performance observations

- Cold start to usable Today:
- Live/map usable:
- Light/dark and outdoor readability:
- Safe-area/gesture overlap:
- Dock or modal overlap:
- Long Chinese names / large text:
- Heat, jank, reload or memory pressure:

## Final verdict

`NOT_RUN`

NO-GO items, owner and evidence:

