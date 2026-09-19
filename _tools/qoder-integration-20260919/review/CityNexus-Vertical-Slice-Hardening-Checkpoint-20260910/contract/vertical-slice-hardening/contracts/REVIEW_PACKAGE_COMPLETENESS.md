# Review Package Reproducibility Contract

A CityNexus review checkpoint is evidence only if a reviewer can reproduce its deterministic gates from a fresh extraction.

## Current packaging defect

The reviewed ZIP contains `data/mock/*` at the archive root, but current backend execution also resolves required support under backend-relative locations. The uploaded archive omitted at least:

```text
backend/db/schema.sql
backend/data/mock/wp04_commerce_catalog.json
backend/data/mock/wp04_city_services_overlay.json
```

As a result, a fresh backend pytest collection did not start until unchanged support files were reconstructed from the prior checkpoint.

## Required next-package rule

From a new extraction with no old CityNexus ZIPs/files available, the reviewer must be able to:

```text
cd backend
python -m pytest -q
```

and reproduce the reported deterministic test result once Python dependencies are installed.

## Do

- Package source schema and authoritative deterministic fixture inputs in the exact repository-relative locations consumed by code/tests.
- Prefer one canonical fixture ownership path and refactor callers if duplicate root/backend paths are accidental.
- Document environment variables for optional live tests.
- Keep live-provider tests opt-in.

## Do not

- Depend on a previous checkpoint.
- Depend on the developer's existing `citynexus.db`.
- Include `node_modules`, `.venv`, caches, or generated test debris merely to make an archive huge enough to look serious.
- Claim a fresh-extract gate without actually testing a fresh extraction.

## Acceptance

A packaging test can be as simple as:

1. Create ZIP from intended payload.
2. Extract into a brand-new temporary directory.
3. Run backend deterministic suite from the extracted `backend` directory.
4. Run frontend build/E2E using normal dependency installation/reuse policy.
5. Record commands and results.
