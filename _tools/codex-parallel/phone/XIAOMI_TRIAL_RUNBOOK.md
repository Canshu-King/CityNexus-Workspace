# Xiaomi 13 Ultra final SHADOW trial

Audience: release owner and device tester. This runbook prepares and records a trial; it does not claim the device has passed.

## Entry gate

- Use a clean, named release-candidate branch and record its full SHA. The observed integration snapshot `1a8462d` is detached and is not itself a release branch.
- Re-run focused truth/provider gates on that SHA. Keep payment, unattended mutation and safety-critical mobility decisions disabled.
- Use an HTTPS phone URL. The helper scripts only print HTTP LAN candidates; they do not create TLS, tunnels or firewall rules.
- Configure a trustworthy Valhalla endpoint only in the owner-controlled runtime. Do not put endpoints or credentials in evidence.
- Verify every coordinate in `routing/xiamen_route_pairs.json` before live use.

## Host preflight

```powershell
.\preflight_windows.ps1
.\collect_host_state.ps1
```

Confirm backend/frontend listen on LAN-capable addresses. A listener bound only to `127.0.0.1` is not phone-reachable. Do not change firewall rules from these scripts.

## Fresh-device setup

1. Record Xiaomi 13 Ultra model, Android/HyperOS, browser, display/font scaling, refresh-rate and battery mode.
2. Remove the previous CityNexus PWA, service worker and site storage.
3. Open the HTTPS URL, grant location only when prompted, install the PWA, then launch standalone.
4. Confirm status bar, camera cutout and bottom gesture area do not cover controls.

## Mandatory product chain

Capture the IDs and screenshots in `PHONE_EVIDENCE_TEMPLATE.md`.

1. **Create** a new Xiamen Journey with Asia/Shanghai timezone.
2. **Plan** using real discovered places; record the plan version.
3. **Select** exactly one active/chosen plan.
4. **Hotel**: inspect and select a stay without silently changing the active plan.
5. **Booking**: import/confirm a simulated reservation and verify identity, currency and schedule.
6. **Copilot**: ask for an explanation; confirm it does not mutate before approval.
7. **Map**: verify provider-backed route evidence and honest location-denied/error states.
8. **Live**: verify current/next stop and mobility provenance.
9. **Disruption**: inject a controlled closure/delay linked to a real trigger event.
10. **Provider-backed material replan**: proposal must have a meaningful diff and only hard-eligible mobility facts.
11. **Accept** once; repeat the request/reload and prove idempotency.
12. **Agreement**: Today, Trips and Live show the same active plan, proposal result and booking protection.

Run the complete chain twice: once after fresh install and once after killing/reopening the PWA. The second run must not rely on accidental stale cache.

## Fault checks

- Deny location, then grant it later.
- Disconnect/reconnect Wi-Fi during SSE activity.
- Make one route leg unavailable, then all candidates unavailable.
- Return a malformed provider response in the controlled fault harness.
- Trigger duplicate Accept and duplicate booking import.
- Exercise light/dark, 360/412/430-equivalent widths, large text and outdoor brightness.

## Immediate NO-GO

- Mock/replay mobility becomes hard truth or is labelled `LIVE_PROVIDER_CAPTURE`.
- Stale evidence is presented as current.
- Raw enum, stack trace or provider error leaks into primary UI.
- Today, Live or Trips is blank or disagrees about the active plan.
- Copilot dock covers a primary action/content; avatar/text overflows materially.
- Provider provenance is missing from a hard mobility decision.
- Accepted proposal has no material diff, changes protected bookings, or applies twice.
- `MOBILITY_DATA_UNAVAILABLE` is replaced by an invented ETA or acceptable proposal.
- Fresh install cannot complete the chain.

## Exit

Export the evidence template, console/backend logs, sanitized provider request/response, screenshots/video, commit and artifact hashes. Verdict is only `PASS`, `FAIL`, or `NOT_RUN`; never infer PASS from desktop automation.
