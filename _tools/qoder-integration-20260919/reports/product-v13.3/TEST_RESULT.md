# V13.3 Test Result

## Focused

- Repository V13.3 prep, real-city, V13.2, and V10 focused set: `12 passed`.
- Supplied V13.3 prep starter checks: `3 passed`.
- Frontend `npm run build`: PASS.

## Browser

- Playwright CLI City Discovery flow: PASS.
- Discovery result showed sealed replay provenance and deterministic feasibility.
- Authoritative handoff showed the selected PlanVersion activities and frozen evidence.

## Broad convergence

`385 passed, 2 skipped, 2 warnings in 38.19s`.

The two initial convergence failures were corrected before this final run: OpenAPI parity now includes the V13.3 intelligence route, and the V10 vision fake seam remains compatible while production selects the dedicated vision model.

## Fresh extraction

The corrected release archive was extracted to a new directory with no root staging directories. Against the extracted source, the targeted backend gate passed `12 passed`, and a fresh `npm ci --ignore-scripts --no-audit --no-fund` followed by `npm run build` passed. The fresh backend runtime used an isolated SQLite file and no AI key.
