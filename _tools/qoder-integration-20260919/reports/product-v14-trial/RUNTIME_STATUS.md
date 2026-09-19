# Runtime and Release Status

## Services left running

The final source tree was launched with FastAPI bound to `127.0.0.1:8000` and Vite bound to `127.0.0.1:5173`. The browser trial used the live frontend URL and the backend API through the Vite proxy.

## Provider labels

`CITYNEXUS_REAL_CITY_ENABLED=true` was applied to the launched backend process. No DeepSeek API key was present in the Windows environment visible to this task, and no key was written to the repository or release staging area. No `CITYNEXUS_LIVE_VALHALLA_URL` was configured, so the application makes no live-traffic claim.

The Tianjin sealed demo remains explicitly labelled `SEALED_REAL_REPLAY`. Generic-city failure is represented as live-provider unavailability, not as a replay fallback from a different city.

## Packaging hygiene

The release staging copy excludes `.git`, virtual environments, `node_modules`, frontend build output, runtime output, test caches, SQLite databases and `*.db-wal`/`*.db-shm` sidecars, environment files, key/certificate files, logs, and nested archives. The final archive contains the trial reports and browser evidence screenshot but no secret material.

