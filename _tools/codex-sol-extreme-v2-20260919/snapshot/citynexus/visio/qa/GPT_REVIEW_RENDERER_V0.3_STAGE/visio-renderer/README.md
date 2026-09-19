# CityNexus deterministic Visio renderer

`render_phase1.py` reads page YAML and creates native Visio UML masters. Shape and connector identity is always the YAML `id`, persisted as `Prop.SpecId`; collection order is never used for semantic resolution. Coordinates use the required center-based cm-to-inch conversion.

`validate_rendered_vsdx.py` independently reads the VSDX package/XML and rejects forbidden ShapeSheet error tokens. It is intentionally separate from renderer claims.

Run one page at a time with the Style Guide gate first. Do not render Part 2.
