# Repo-relative mapping

The checkpoint is self-contained under this directory. Implementation paths
are under `implementation/` and the exact supplied contract/evidence is under
`review_contract/source/`.

| Checkpoint path | Source path in the working tree |
| --- | --- |
| `implementation/.env.example` | `.env.example` |
| `implementation/backend/` | `backend/` (source, schema, fixtures, tests, and `pyproject.toml`; generated databases/caches omitted) |
| `implementation/contracts/openapi.yaml` | `contracts/openapi.yaml` |
| `implementation/data/` | `data/` (fixture data) |
| `implementation/requirements/` | `requirements/` (pre-existing baseline and reports; hash-named artifacts omitted) |
| `implementation/frontend/` | `frontend/` (package manifests, source, contract types, e2e test; `node_modules`, `dist`, and test output omitted) |
| `review_contract/source/` | `_incoming_wp06_wp07_road_prep_20260909/CityNexus_WP06_WP07_Road_Prep_20260909/` |

The checkpoint root documents and `evidence/` files are generated review
metadata. They do not introduce runtime import paths.

