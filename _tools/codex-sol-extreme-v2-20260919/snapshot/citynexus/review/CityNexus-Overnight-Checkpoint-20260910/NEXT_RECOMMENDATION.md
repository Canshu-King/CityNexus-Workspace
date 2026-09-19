# Next recommendation

1. Have GPT independently review `OVERNIGHT_REPORT.md`, the Road-Prep contract,
   and the deterministic backend evidence before merging or enabling any live
   provider.
2. After acceptance, connect the existing frontend shell to the current
   OpenAPI Journey/Twin/Replan endpoints using mock/frozen fixtures first;
   retain the backend as the sole source of Journey, PlanVersion, Commitment,
   payment, and feasibility truth.
3. If operational credentials become available, run one bounded Valhalla or
   Open-Meteo smoke and freeze the returned facts into snapshots before gate
   use. Keep provider failures on the tested degraded/fallback path.
4. Add CI coverage for the optional OR-Tools and LiteLLM adapters only in
   opt-in jobs, and complete the remaining conservative requirement traceability
   review.

Do not start a later work package or make external services mandatory until
this checkpoint is externally accepted.

