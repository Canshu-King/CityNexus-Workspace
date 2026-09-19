# Evidence Scope

Accessibility evidence is evaluated against the requested requirement. `toilets:wheelchair=yes` is toilet evidence only; `ramp=yes` and `elevator=yes` are partial evidence and do not prove a complete step-free place or route. Unknown evidence is never treated as accessible. Route-level step-free requires a real route/provider assertion.

Both mapping tags and OSM `key=value` list/tuple forms are normalized before evaluation. Stairs conflict wins over positive partial signals.
