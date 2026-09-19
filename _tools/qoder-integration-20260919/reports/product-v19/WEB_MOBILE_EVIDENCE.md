# Web and Mobile Evidence

The existing responsive Copilot/event experience remains intact. The TravelerTwin panel now renders persisted explicit capability facts, severity, confirmation state, and the hard-vs-learned boundary. It no longer renders fabricated `0.88`/`0.42` strength bars or fallback dimensions when the API has no data.

The frontend production build passed once after the V19 changes. The build measured the existing split output: main JavaScript about 1,038 kB gzip 304 kB, MapLibre chunk about 1,053 kB gzip 285 kB. MapLibre remains separately chunked by the existing setup.

No native Hermes browser flow is claimed in this convergence because runtime status was `NATIVE_DEEPSEEK_TOOL_LOOP` with `hermes_native_gateway.ready=false`. This is recorded rather than replaced by a recorded fixture.
