# V13 Review Archive Manifest

Target archive:

`CityNexus-V13-Authoritative-Integrity-Commitment-Recovery-20260913.zip`

The curated archive is assembled from the current worktree after the hard
8-hour wall-clock gate. It includes these source families:

- `backend/app`, `backend/db`, `backend/tests`, and `backend/pyproject.toml`;
- `frontend/src`, `frontend/public`, `frontend/e2e`, Storybook sources, and
  frontend manifests/configuration;
- `agent-mcp/citynexus_mcp`, its tests, contract example and project metadata;
- `contracts`, `data/mock`, `data/v9`, and the sealed
  `data/replay/tianjin_real_snapshot.json`;
- `scripts`, `tools`, `evals/promptfoo`, and all `reports/product-v13`
  evidence including the three authoritative browser screenshots.

It intentionally excludes API keys and secret-bearing environment files,
databases/WAL files, caches, virtual environments, `node_modules`, frontend
`dist`/`storybook-static`, Playwright raw dumps/traces, nested historical ZIPs,
and temporary extracted archives. The archive is then fresh-extracted outside
the repository and checked for the same exclusions before it is reported.

## Final validation

- Archive: `D:\moodle\CityNexus\CityNexus-V13-Authoritative-Integrity-Commitment-Recovery-20260913.zip`
- Archive entry count: `318`
- Archive byte size: `1,030,911` bytes for the final validated compression pass.
- Fresh extract: `D:\moodle\_v13_fresh_extract_20260913_final`
- Validation: **VALIDATED** — required source/report entries present, forbidden secret/database/cache/build/nested-archive entries absent, and fresh-extract Python compilation passed.

No SHA-256 bookkeeping is part of this campaign.
