# V13.1 Fresh-Extract Runtime Gate

## Gate definition

This report is complete only when the final ZIP is extracted to a new empty
directory and the extracted source itself runs the required backend tests and
frontend build. File-count, compile-only, and main-worktree-only evidence is
insufficient.

## Final extraction

- Archive: `D:\moodle\CityNexus\CityNexus-V13.1-Release-Integrity-Temporal-Semantics-20260913.zip`
- Fresh directory: `D:\moodle\_v131_final_release_extract_20260913`
- Forbidden content check: secrets, `.env`, databases/WAL/SHM, caches,
  virtual environments, build output, and nested ZIPs absent.

## Runtime commands and final result

The final run executed from the fresh extraction with the real Windows project
environment. The original repository virtual environment was used only as the
Python runtime; imports and application files came from the fresh extraction.

- Python compile/import smoke: **PASS**;
- WP04 order/pricing, WP04 endpoint, V12, V13, Agent principal/runtime/
  authority, and contract focused scope: **73 passed, 2 warnings** in `16.91s`;
- backend full regression from the fresh `backend/`: **369 passed, 2 skipped,
  2 warnings** in `37.46s`;
- fresh frontend `npm ci --no-audit --no-fund`: **PASS**, 708 packages in `8s`;
- fresh frontend production build: **PASS**, Vite 7.3.6, 1,897 modules,
  built in `4.74s`;
- fresh full Playwright matrix: **16 passed** in `36.5s`;
- fresh layout proof: `root_catalog=True backend_data_directory=False`;
- forbidden-entry scan: **PASS**, no secrets, `.env`, database/WAL/SHM,
  cache, virtual-environment, build-output, or nested ZIP entries.

This is the authoritative V13.1 release gate: **PROVEN FROM FRESH EXTRACT**.
