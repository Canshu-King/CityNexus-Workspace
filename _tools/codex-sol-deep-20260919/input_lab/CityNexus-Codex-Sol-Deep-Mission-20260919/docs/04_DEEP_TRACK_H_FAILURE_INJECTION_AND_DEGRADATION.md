# Deep Track H — Failure injection / graceful degradation architecture

Goal:
Prove CityNexus fails honestly when providers, AI, network, or data are partial.

Build a matrix covering:
- routing provider timeout / 5xx / malformed response
- place provider timeout / duplicate/ambiguous identity
- AI unavailable / slow / malformed structured output
- booking import partial/malformed
- offline/read-only frontend
- stale journey/session state
- map tile failure
- repeated user action / retry / duplicate POST

For each:
- expected backend status / error classification;
- whether data may be cached;
- what must never be fabricated;
- expected consumer copy;
- allowed retry behavior;
- telemetry/evidence required.

Create isolated executable fault-injection tests where practical.

Deliver:
- `reports/DEGRADATION_CONTRACT.md`
- `reports/FAILURE_INJECTION_RESULTS.md`
- `artifacts/failure_matrix.json`
- targeted reproducible tests for any discovered defect.

Priority:
truthfulness > graceful UX > convenience.
No fake provider success.
