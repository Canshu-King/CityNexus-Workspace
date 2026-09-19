# Weather Runtime Hardening Freeze Gate

Weather Runtime can be externally frozen only after the original WRT gate and the following additional checks pass.

## WRH checks

- WRH-01 malformed Open-Meteo parallel arrays fail closed
- WRH-02 provider Event persists snapshot capture timestamp
- WRH-03 forecast validity is separate from decision/detection time
- WRH-04 a successful same-bucket clean forecast resolves a prior active weather risk
- WRH-05 repeated same-identity forecast refreshes trusted evidence without duplicating Event identity
- WRH-06 downstream Replan/MobilitySnapshot uses provider capture time, not future forecast validity

## Required regressions

- WRT-01..WRT-12
- Provider Runtime PRT-01..08
- Provider Hardening PRH-01..05
- Backend Golden Scenario
- full backend pytest with clean exit
- compileall
- Ruff check + format check
- OpenAPI parity
- frontend build / backend-connected Playwright if touched

## Authority assertions

- forecast valid time is not silently treated as current Journey time
- provider evidence carries both observation/capture time and validity interval
- successful explicit coverage may resolve stale provider risk
- provider failure may not resolve stale provider risk
- re-polling changes evidence without generating an event storm
- C4 remains authoritative
- no live weather call inside feasibility or Twin GET
