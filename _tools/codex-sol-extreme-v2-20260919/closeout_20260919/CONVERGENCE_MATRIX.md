# Current-Line Convergence Matrix

Read-only current line: `D:\moodle\_qoder_integration_20260919` at `0af1905f4ed8b7278df05479dc446e0cc7dec6a8`. Pre-existing untracked packaging helpers were observed and not modified.

## Verified Sol findings

| Finding | Current-line status | Authoritative files | Sol candidate change | Current-line behavior / semantic conflict | Recommended minimal integration action |
|---|---|---|---|---|---|
| CX-SOL-001 — stale execution cursor fabrication | **STILL_OPEN_CURRENT_LINE** | `backend/app/operations/v9.py`; `frontend/src/app/V8Experience.tsx` | Backend distinguishes absent from stale; Live fails closed for unknown and uses first non-terminal for null | `_execution_truth()` treats both absent and unknown as `current_index is None` and falls back. `nextActivityOf()` falls back to activity index 1 when the cursor is unknown. This can fabricate Now/Next. | Port the backend stale/absent distinction and the Live window helper plus six cursor regressions. Preserve current Qoder UI structure. |
| CX-EXT-002 — concurrent same-key idempotency race | **STILL_OPEN_CURRENT_LINE** | `backend/app/main.py`; `backend/app/commerce/service_impl.py` | Journey-scoped process-local lock wraps full accept and transaction operations | Current line checks `IdempotencyKey` before mutation but has no Journey-scoped serialization around accept/payment; concurrent sessions can both pass the read. The unrelated `_trip_studio_accept_lock` does not cover these paths. | For the present single-worker reference deployment, port the scoped guard and `PROCESS_LOCAL_ONLY` warning. For production, use DB/advisory/distributed serialization. |
| CX-EXT-003 — competing accepts create multiple ACTIVE plans | **STILL_OPEN_CURRENT_LINE** | `backend/app/main.py::_accept_replan_impl` | Serialize acceptance before proposal/base-plan validation and competitor invalidation | Current line invalidates competitors after activating the winner, but two requests can validate the same base concurrently before either commits. | Put the complete acceptance transaction under Journey serialization; keep competitor invalidation and existing feasibility revalidation. |
| CX-EXT-004 — CAPTURE vs ACCEPT leaves dangling C4 identity | **PARTIALLY_FIXED** | `backend/app/main.py`; `backend/app/commerce/service_impl.py`; `backend/app/replanning/protected_commitments.py` | Serialize capture/accept; remap capture to the active plan; require one unique semantic/time match | Accept already remaps C4 references, but selects the first matching Activity. Capture has neither active-plan remap nor common Journey serialization. Ambiguous matches and the cross-operation race remain. | Keep current C4 preservation, replace first-match selection with unique-match fail-closed logic, call the same semantic remapper on successful capture, and serialize both paths. |

## Related truth surfaces

| Surface | Current-line status | Evidence / integration ruling |
|---|---|---|
| Mobility provenance / hard truth | **ALREADY_FIXED_CURRENT_LINE** | `HARD_FEASIBLE_QUALITIES` is an exact allowlist and hard capture uses `fallback=None`; retain current Qoder implementation. |
| Physical identity | **ALREADY_FIXED_CURRENT_LINE** | `compare_physical_venue()` and provider-scoped identity rules are present; do not replace them with generic place/service overlap. |
| C4 preservation | **PARTIALLY_FIXED** | Replan acceptance preserves/remaps C4, but ambiguity and payment-race convergence remain open as above. |
| Replan acceptance serialization | **STILL_OPEN_CURRENT_LINE** | Idempotency is persisted, but the check-and-write transaction is not serialized. |
| Booking/payment serialization | **STILL_OPEN_CURRENT_LINE** | Payment duplicate checks and C4 upgrade are not in the same Journey critical section as acceptance. |
| E2E acceptance policy | **ALREADY_FIXED_CURRENT_LINE** | `docs/E2E_ACCEPTANCE_POLICY.md` requires authoritative provenance and rejects `reuseExistingServer: true`; retain this policy. |

## Reconciliation order

1. Preserve current-line mobility, physical-identity, and E2E authority contracts.
2. Port stale-vs-absent backend cursor semantics.
3. Port the Live first-non-terminal/fail-closed projection without redesigning the UI.
4. Add Journey-scoped single-worker serialization and its explicit production limitation.
5. Harden both accept-time and capture-time C4 remap to require one unique semantic/time match.
6. Run current-line focused truth tests, five race schedules, projection/browser gates, then the authoritative E2E policy gate.
