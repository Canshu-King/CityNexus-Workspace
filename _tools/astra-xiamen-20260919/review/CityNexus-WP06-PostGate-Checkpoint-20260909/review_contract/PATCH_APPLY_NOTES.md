# Patch Apply Notes

Patch:

`patches/CityNexus_WP06_PostGate_Hardening_and_ProviderPrep_20260909.patch`

## Important

The patch was generated against the reviewed checkpoint, not against an unknown later local workspace.

On `D:\moodle\CityNexus`:

1. inspect current working-tree changes;
2. do **not** reset/rollback newer work;
3. run `git apply --check <patch>` if the local tree still matches;
4. if it passes, apply it;
5. if it conflicts, use `reference_overlay/` to perform a semantic merge of the same behavior;
6. merge `reference_overlay/contracts/openapi.yaml` carefully instead of blindly replacing a newer local contract.

The unified patch intentionally excludes `contracts/openapi.yaml` because line-ending differences made cross-platform patching brittle. The complete intended OpenAPI overlay is included separately.

## Files touched by patch

- `backend/app/main.py`
- `backend/app/integrations/ai/resilient.py`
- `backend/app/integrations/mobility/snapshot_capture.py`
- `backend/app/integrations/mobility/valhalla_http.py`
- `backend/tests/test_wp04_hardening_wp05.py`
- `backend/tests/test_wp05_integrity_next.py`
- `backend/tests/test_wp06_postgate_hardening_next.py`
- `backend/tests/test_postgate_provider_foundation.py`

## OpenAPI overlay

The overlay documents:

- deterministic optional `now` on JourneyTwin GET;
- replan-generation conflict response;
- replan-reject conflict response;
- the already-formal required Idempotency-Key on replan acceptance now matches runtime.
