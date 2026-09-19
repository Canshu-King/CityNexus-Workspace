# Dependency manifest

The default deterministic gate needs only the existing Python environment and
the dependencies declared by `implementation/backend/pyproject.toml`.

- Python: `>=3.12`
- Backend runtime: FastAPI, Uvicorn, SQLAlchemy, Alembic, Pydantic,
  pydantic-settings, and HTTPX
- Backend development: pytest, pytest-asyncio, and Ruff
- Frontend manifest: `implementation/frontend/package.json`
- Frontend lockfile: `implementation/frontend/package-lock.json`
- Frontend browser profile: Vite, React, MapLibre, Turf, XState, TypeScript,
  the Vite React plugin, and Playwright

Valhalla, Open-Meteo, OR-Tools, LiteLLM, and DeepSeek are optional integration
boundaries. They are not required to install or pass the default offline
tests. The optional AI path is disabled unless `CITYNEXUS_AI_ENABLED=true` and
an API key is supplied; the optional live Valhalla path is disabled unless
`CITYNEXUS_LIVE_VALHALLA_URL` is supplied.

