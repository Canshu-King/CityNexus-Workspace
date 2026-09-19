# Enum and internal-label leak audit

The inspected snapshot has no verified P0/P1 enum leak.

- Disruption values are normalized in `disruptionState`; ACKNOWLEDGED is not rendered as resolved.
- Proposal lifecycle values drive decisions but consumer copy uses localized action/state language.
- Mobility modes have a localized mapping; unknown values fall back to title-cased tokens. That fallback is a P3 forward-compatibility risk, not a current verified leak.
- Provider provenance remains visible only in evidence-oriented surfaces. It is not used as a consumer promise of hard eligibility.
- Budget evidence internal states NONE/PARTIAL/FULL are translated into scoped copy; raw labels are not shown.
- Recovery state values are typed and routed into dedicated UI states.

Recommended guard: add a fixture containing one future/unknown enum value for each public union and assert the UI uses neutral “unavailable/unknown” copy rather than title-casing backend tokens.

