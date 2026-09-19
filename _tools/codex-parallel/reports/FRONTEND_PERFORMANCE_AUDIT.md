# Frontend bundle/performance audit

Read-only snapshot at integration `1a8462d`. No frontend files were edited and no new build was run in the protected tree.

## Measured facts

| Asset | Minified raw | Gzip evidence | Loading implication |
| --- | ---: | ---: | --- |
| Main `index-*.js` | 1,126,849 B | 333.99 kB | Still above Vite's 500 kB warning and paid by the V8 shell |
| `maplibre-gl-*.js` | 1,053,381 B | 284.76 kB | Separate dynamic chunk, but included in PWA precache |
| `JourneyMap-*.js` | 4,392 B | 1.80 kB | Legacy recovery wrapper is lazy |
| CSS | 161,563 B | 28.96 kB | Single global CSS payload |
| PWA precache | 9 entries / 2,292.33 KiB | build log | Install/update downloads both large JS assets even if first view has no map |

The existing V18.3 optimization is real: MapLibre moved out of initial JS and initial raw JS roughly halved versus V18.2. The remaining debt is the monolithic application shell and PWA precache policy, not failure to split MapLibre at all.

## Source concentration

- `V8Experience.tsx`: 2,716 lines / ~102 KB and statically imports almost every product surface.
- `main.tsx`: 1,682 lines / ~68 KB.
- `LocaleContext.tsx`: 1,347 lines / ~65 KB with both locale dictionaries.
- `citynexus.ts`: 1,072 lines / ~31 KB.
- Eager V8 imports pull Copilot, Inbox, QR scanner, Trip Studio/dnd-kit, stays, planning, recovery and discovery into the main graph.
- Heavy dependencies found: `@zxing/browser`, `@dnd-kit/*`, Dexie and XState. `MapPanel` dynamically imports MapLibre; `JourneyMap` statically imports it but is itself React-lazy.

## Risks

- Large main parse/evaluate cost on Xiaomi-class mobile even when gzip transfer is acceptable.
- PWA updates precache ~2.29 MiB, reducing the network benefit of dynamic MapLibre for fresh installs.
- Splitting without stable loading/error boundaries could blank Today/Live or break offline behavior.
- Blind `manualChunks` can create circular/shared-chunk churn and is lower value than feature boundaries.

## Measurement gate for future work

Record before/after main raw+gzip, precache bytes, cold navigation to Today and Live, first map interaction, offline revisit, chunk request waterfall and Xiaomi memory/jank. Do not merely raise `chunkSizeWarningLimit`.
