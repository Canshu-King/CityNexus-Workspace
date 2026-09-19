# CityNexus V13.1 Release Manifest

- Archive: `D:\moodle\CityNexus\CityNexus-V13.1-Release-Integrity-Temporal-Semantics-20260913.zip`
- Fresh extraction: `D:\moodle\_v131_final_release_extract_20260913`
- Included: backend application/schema/tests, frontend source/config/tests,
  Agent MCP source/tests, contracts, canonical `data/`, evaluation/tooling,
  preserved V13 reports/evidence, and all V13.1 reports.
- Excluded: `backend/data` duplicate, `.env`/secret files, databases and
  WAL/SHM files, caches, virtual environments, `node_modules`, frontend build
  output, Playwright raw results, and nested archives.
- Validation: **PROVEN FROM FRESH EXTRACT** — 73 focused tests, 369 full
  backend tests with 2 existing skips, production build, and Playwright 16/16.
