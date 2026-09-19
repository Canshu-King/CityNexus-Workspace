# CityNexus Provider Runtime Hardening Checkpoint

Date: 2026-09-10

## Gate status

Provider Runtime Gate = **FROZEN_PASS**

This checkpoint closes the five externally identified Provider Runtime semantic defects while preserving the existing PRT-01..PRT-08 behavior.

## Closed defects

- PRH-01: `MobilitySnapshot.facts` is structurally immutable through a defensive copy wrapped in `MappingProxyType`; snapshot key/fact identity is validated.
- PRH-02: JourneyTwin reports the effective fact provider for the C4 buffer and separately preserves `source_provider`, snapshot degradation, fact degradation, snapshot id, and fallback reason.
- PRH-03: degraded mobility is propagated into before/after `FeasibilityEnvelope` evidence and verified robustness scoring.
- PRH-04: base and candidate route totals are both recomputed under the same frozen `MobilitySnapshot` before `travel_delta_min` is calculated.
- PRH-05: accept-time revalidation reconstructs and injects the persisted proposal `MobilitySnapshot`; no implicit default mock provider is used.

## Scope boundary

No Open-Meteo runtime attribution, OR-Tools, AI ranking, MapLibre polish, Visio, or PPT work was started in this mutation batch.

## Architecture preserved

`Provider fact -> frozen evidence -> deterministic feasibility -> verified scoring -> user confirmation`

Durable C4 commitments remain authority. JourneyTwin remains a projection. Providers, solvers, and AI do not become the decision authority.

## Review status

Local freeze gates are green. This package is intended for fresh-extract external review before Weather Runtime work begins.
