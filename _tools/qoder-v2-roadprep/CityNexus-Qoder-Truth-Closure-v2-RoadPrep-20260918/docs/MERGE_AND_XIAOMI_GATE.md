# Merge and Xiaomi Gate

## Stage 1 — Qoder v2

Stay isolated.
Do not write the authoritative tree.

Return:

`CityNexus-Qoder-Xiaomi-Truth-Hardening-v2-20260918.zip`

Verdict:
- `QODER_V2_PATCH_READY_FOR_INTEGRATION`
or
- `QODER_V2_BLOCKED`

## Stage 2 — freeze authoritative repository

Before merge, create a real source-control baseline for the current CityNexus
state.

Do NOT commit:
- secrets / API keys / .env
- runtime DBs
- node_modules
- caches
- generated screenshots/evidence unless intentionally versioned

Then apply/reconcile the approved Qoder v2 patch.

## Stage 3 — authoritative integration tests

Run on the real integrated code:
- T1-T4 focused suite
- existing replan / guardian / booking truth tests
- frontend typecheck/build
- visible Xiaomi-like browser chain

## Stage 4 — live mobility provider gate

A truth-safe fail-closed system may enter an engineering smoke test.

A **full real-user Xiaomi dynamic-replan trial** should additionally have a
trustworthy routing provider configured (for example the already-supported
Valhalla path), or explicitly disable dynamic auto-replan when live routing is
unavailable.

Required live-provider smoke:
- several real Xiamen pairs return provider-backed durations;
- provenance is visible as live/provider capture;
- provider outage falls back to honest unavailability, not synthetic 20.

## Stage 5 — fresh Xiaomi trial trace

One fresh same-Xiamen journey:
- create
- plan/select
- hotel
- confirmed booking
- Copilot
- map
- closure on mutable POI
- material replan using trustworthy mobility
- UI accept
- final Trips/Live agreement

No stale evidence.

## Hard blockers before full Xiaomi trial

1. T2 real-path fabricated-20 bypass closed.
2. No full-budget claim from incomplete trip-cost scope.
3. ACK-only state proven consistent in rendered Today/Live.
4. replacement identity cannot reintroduce the same closed venue through a
   cross-provider alias.
5. authoritative integrated branch exists and passes focused gates.
6. dynamic replan has trustworthy routing, or the trial explicitly treats it as
   unavailable rather than pretending it works.

## Not hard blockers for the first controlled Xiaomi trial

- Frontend vNext refactor
- optional offline/wallet timezone cleanup, if trial scope is documented
- global create-idempotency architecture, provided duplicate creation is watched
  and not represented as solved
- visual polish beyond the current consumer gate
