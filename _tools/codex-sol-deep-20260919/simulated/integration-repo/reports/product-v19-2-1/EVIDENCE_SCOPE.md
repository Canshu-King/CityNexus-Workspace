# Evidence Scope

Accessibility evidence is requirement-specific. Toilet tags do not prove
step-free access; ramps/elevators do not prove a complete route; route-level
step-free remains `NEEDS_LIVE_EVIDENCE` without route proof. Mapping and
list/tuple OSM tag forms are normalized. Unknown evidence never becomes an
accessible assertion.

Capability confirmation uses PUT as full replacement and POST confirm as
submitted-item upsert. Duplicate transport confirmation references are
rejected by the journey-scoped uniqueness constraint.
