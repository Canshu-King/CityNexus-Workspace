# WP00 domain reconciliation

Date: 2026-09-09  
Contract: CityNexus MVP Implementation Blueprint v0.1  
Frozen source: CityNexus Core Domain Model v0.4.2 RC3

## Read-only evidence

The frozen source files were read without modification. This checkpoint records
the reconciliation findings and executable behavior for the repair cycle.

## Exact source entity list (18)

`Traveler`, `Journey`, `JourneyTwin`, `PlanVersion`, `Activity`, `Place`, `CityService`, `Commitment`, `Constraint`, `Event`, `ContextSnapshot`, `ReplanProposal`, `CandidatePlan`, `Booking`, `Order`, `PaymentTransaction`, `Recommendation`, `Preference`.

## Naming and lifecycle reconciliation

The blueprint intentionally preserves a handoff naming gap: its source-backed list names `Transaction`, while the promoted YAML names the entity `PaymentTransaction`. The implementation will use the blueprint API and SQL contract name `transactions` for the technical persistence table and will treat it as the `PaymentTransaction` domain concept when WP04 is reached.

The blueprint omits two entities because their names were not available in the handoff. The local YAML identifies them exactly:

| Local entity | MVP decision |
| --- | --- |
| `ContextSnapshot` | Not needed for WP01-WP03. It remains a source-of-truth projection input reserved for WP05/WP06; no substitute entity is invented. |
| `CandidatePlan` | Not persisted for WP01-WP03. Initial candidates are executable `PlanVersion` records with `CANDIDATE` status, as required by the package API. The dedicated source entity remains reserved for WP06 replan proposals. |

The package's executable API/SQL contract uses uppercase lifecycle values (`DRAFT`, `CANDIDATE`, `ACTIVE`, etc.) and an intermediate `SELECTED` plan state. The source YAML uses lowercase state names and does not define `SELECTED`; these are implementation representations introduced by the package, not edits to the frozen baseline. WP01-WP03 therefore follow the package contract exactly at the API boundary, while this mapping is recorded for later domain-level translation:

- source `draft/planned/active` ↔ package `DRAFT/PLANNED/ACTIVE`;
- source `candidate/active/superseded/rejected` ↔ package plan lifecycle values;
- source activity `proposed/scheduled/in_progress` ↔ package `PLANNED/READY/ACTIVE`;
- source commitment strengths `C0_Flexible`…`C4_Anchored` ↔ package `FLEXIBLE/RESERVED/PAID/LOCKED`.

The source `planning_mode` values match exactly: `balanced`, `budget`, `explore`, `strict_schedule`. The repaired implementation persists the requested mode on `Journey` and uses it as the default for subsequent plan generation.

## MVP capability traceability used by WP00-WP03

The real requirements baseline was read far enough to anchor the first packages. The primary IDs are:

- traveler/preferences: `FR-001`–`FR-007`, `FR-011`;
- constraints and planning: `FR-008`–`FR-014`, `FR-024`–`FR-025`;
- discovery: `FR-018`–`FR-023`, `FR-028`;
- deterministic/provider boundaries: `BR-005`, `BR-008`, `BR-019`–`BR-021`, `IR-001`–`IR-004`, `IR-011`–`IR-012`;
- traceability goals: `BG-001`, `BG-002`, `BG-005`, `BG-006`, `BG-007`.

The corresponding source use cases are `UC-01 Manage Account & Preferences`, `UC-02 Create & Configure Journey`, `UC-04 Generate & Select Journey Plan`, and `UC-05 Discover & Recommend City Services`.

## WP00 result

Frozen domain, requirements and Visio files remain untouched. The application folders were added at the repository root, the package OpenAPI contract was copied to `contracts/openapi.yaml`, and the package environment example was copied to `.env.example`. No implementation depends on internet access.
