# Repo-relative mapping

The checkpoint preserves the exact repository-relative layout:

- `backend/app/**` -> `backend/app/**`
- `backend/data/**` -> `backend/data/**`
- `backend/db/**` -> `backend/db/**`
- `backend/tests/**` -> `backend/tests/**`
- `backend/pyproject.toml` -> `backend/pyproject.toml`
- `contracts/openapi.yaml` -> `contracts/openapi.yaml`
- `data/**` -> `data/**`

The source review package and the applied reference patch are retained under `assist-contract/` as review evidence only; they are not runtime paths.
