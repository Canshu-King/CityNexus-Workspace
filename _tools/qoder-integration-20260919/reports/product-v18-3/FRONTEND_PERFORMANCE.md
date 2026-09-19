# Frontend performance convergence

Measurements were taken from the production Vite output in
frontend/dist/assets. Gzip values use the same local PowerShell GZipStream
measurement for comparable raw assets.

| Metric | V18.2 baseline | V18.3 result |
| --- | ---: | ---: |
| Initial JS raw | 2,106,778 B | 1,036,966 B |
| Initial JS gzip | 599,372 B | 307,196 B |
| MapLibre chunk raw | included in initial | 1,053,381 B |
| MapLibre chunk gzip | included in initial | 286,800 B |
| Recovery JourneyMap chunk | included in initial | 4,338 B |
| CSS raw | 132,823 B | 132,917 B |
| CSS gzip | 24,031 B | 24,045 B |

V18.3 dynamically imports MapLibre in MapPanel and lazy-loads the legacy
recovery JourneyMap. The non-map entrypoint does not statically import
MapLibre; Vite emits maplibre-gl-* and JourneyMap-* chunks. Map/WebGL
initialization occurs only after a map surface mounts.

The remaining large-chunk advisory applies to the intentionally isolated map
chunk, not the initial Copilot/Journey shell. No warning threshold was raised
to hide the measurement.
