# Track C — Xiaomi 13 Ultra trial tooling

Create:
- `phone/XIAOMI_TRIAL_RUNBOOK.md`
- `phone/PHONE_EVIDENCE_TEMPLATE.md`
- `phone/preflight_windows.ps1`
- `phone/collect_host_state.ps1`

Safe scripts may:
- list host LAN IPs;
- list backend/frontend listening ports;
- call local health endpoints;
- show commit/version/environment state;
- print the test URL for the phone;
- save logs under the isolated Codex output tree.

They must NOT:
- alter firewall rules;
- install drivers;
- enable ADB;
- alter Android;
- touch the main repo.

Runbook chain:
create -> plan -> select -> hotel -> booking -> Copilot -> Map -> Live ->
disruption -> provider-backed material replan -> accept ->
Today/Trips/Live agreement.

NO-GO examples:
mock hard fallback, stale evidence, raw enum/error leakage, blank primary page,
dock overlap, missing live provenance, accepted proposal with no material diff.
