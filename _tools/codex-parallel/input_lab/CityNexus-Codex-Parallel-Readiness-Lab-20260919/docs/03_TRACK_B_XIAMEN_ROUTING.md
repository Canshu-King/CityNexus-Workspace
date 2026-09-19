# Track B — Xiamen live routing / Valhalla preflight

Prepare tooling only. Do not deploy or enable external infrastructure.

Create under `D:\moodle\_codex_parallel_20260919\routing\`:

1. `xiamen_routing_smoke.py`
   - base URL/config via env/CLI;
   - provider health check;
   - several Xiamen route pairs;
   - record request, response, duration, provider/provenance;
   - JSON + Markdown output;
   - no credentials hardcoded.

2. `xiamen_route_pairs.json`
   Representative:
   - Xiamen Gaoqi Airport -> central hotel/POI zone
   - Xiamen North Railway Station -> central hotel/POI zone
   - hotel/urban point -> ferry/terminal-side point
   - hotel -> POI
   - POI -> POI
   Use project-known coordinates where supported; otherwise explicit placeholders.

3. `routing_failure_injection_plan.md`
   Prove later:
   - one failed live leg excludes only its candidate;
   - another fully-live candidate may survive;
   - all unavailable -> MOBILITY_DATA_UNAVAILABLE;
   - mock fixture never becomes hard truth.

4. `routing_env.example`
   Placeholder names only.
