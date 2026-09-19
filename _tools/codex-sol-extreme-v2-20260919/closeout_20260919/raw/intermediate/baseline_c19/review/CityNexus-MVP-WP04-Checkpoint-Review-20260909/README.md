# CityNexus MVP WP04 checkpoint review

Date: 2026-09-09  
Workspace: `D:\moodle\CityNexus`  
Contract: `CityNexus-WP04-Preflight-Assist-20260909.zip`, with
`CODEX_WP04_START_INSTRUCTION.md`, `11_INTEGRATION_PATCH_MAP.md`, and
`10_WP04_WORK_PACKAGE.md` read in that order.

## Scope and stop condition

WP03 was accepted before this run and was not reopened or redesigned. The
requested WP04A-0 bridge was completed first, followed by the supplied WP04A
through WP04G order. This checkpoint stops at the WP04 STOP Gate; WP05 was not
started.

The bridge covers duplicate semantic locations (stable identity plus scheduled
relative start), planned-Journey currency revalidation in the shared
deterministic feasibility layer, and no-op selection of the already-current
SELECTED PlanVersion without a second `plan.selected` audit.

## Frozen source reconciliation

The local v0.4.2 Domain YAML was read before WP04A. The exact values and order
are recorded in `evidence/source-reconciliation.md` and are used by generated
source modules, SQL, API validation, and commitment policy mapping:

- `commitment_strength`: `C0_Flexible`, `C1_Preferred`, `C2_Reserved`,
  `C3_Guaranteed`, `C4_Anchored`
- `commitment_source_type`: `user_lock`, `booking`, `payment`,
  `external_schedule`

## Gate result

- Full workspace suite: **87 passed**, 2 dependency deprecation warnings.
- Supplied archive tool suite: **5 passed**.
- Ruff check: **PASS**.
- Ruff format check: **PASS**.
- Supplied WP04 preflight: **PASS**, `p0=0`, `p1=0`.
- OpenAPI parse/route smoke: **PASS**; 33 contract paths and all seven WP04
  routes are present.
- Fresh-process persistence smoke: **PASS**; confirmed booking, succeeded
  capture, active `C4_Anchored` commitment, and provider external reference
  survived a new application/session process.

The canonical River Cruise witness reaches C4 only after provider-confirmed
booking plus successful capture and fixed/user-anchor evidence. A paid flexible
order remains below C4. No card credentials, live network provider, or real
payment gateway was introduced.

See `evidence/gate-report.md` for commands and detailed acceptance evidence,
`evidence/source-reconciliation.md` for the frozen enum read, and
`evidence/wp04-status-addendum.csv` for conservative WP04 status updates.
