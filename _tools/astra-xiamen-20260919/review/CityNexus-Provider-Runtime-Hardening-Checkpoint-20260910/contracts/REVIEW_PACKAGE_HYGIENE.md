# Review Package Hygiene

A review checkpoint should be source-reproducible, not a souvenir of the local
runtime directory.

Exclude:

```text
.venv/
node_modules/
dist/
.pytest_cache/
**/__pycache__/
**/*.pyc
**/*.pyo
**/*.db
**/*.sqlite
**/*.sqlite3
```

Include the files that fresh tests actually need:

```text
backend/app/
backend/tests/
backend/db/schema.sql
backend/data/mock/
data/mock/
contracts/openapi.yaml
frontend/package.json
frontend/package-lock.json
frontend/src/
frontend/e2e/
frontend/playwright.config.ts
frontend/vite.config.ts
relevant docs/reports
```

Do not spend time on SHA-256 review. The useful gate is a fresh extraction that
can actually run the relevant tests.
