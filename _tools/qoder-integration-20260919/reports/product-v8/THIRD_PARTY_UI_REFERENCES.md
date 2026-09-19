# Third-party UI references and adoption record

The V8 visual direction was informed by the supplied `GITHUB_UI_RESEARCH.md` and constrained by `UI_GITHUB_ADOPTION_POLICY.md`.

| Reference | Use | License / handling |
|---|---|---|
| shadcn/ui primitives | Accessible button, card, sheet, and focus patterns | MIT-compatible patterns; no wholesale copy or generated dependency added |
| shadcn-admin | Information-density and sidebar rhythm | MIT reference only; CityNexus shell is original and Journey-specific |
| chatbot-template | Composer hierarchy and human-readable agent progress | MIT reference only; no raw tool JSON in the primary UI |
| react-resizable-panels | Considered for Trip Studio map/timeline split | Not added because the current bounded layout is more stable on mobile |
| MapLibre / OpenFreeMap | Map surface and route context | Existing project dependency and public style endpoint; attribution/provenance remains visible |
| Itinera / TripForger | Product visual inspiration only | No unlicensed code or assets copied |

No consumer hotel website was scraped. No third-party visual asset or secret is included in the V8 archive.

