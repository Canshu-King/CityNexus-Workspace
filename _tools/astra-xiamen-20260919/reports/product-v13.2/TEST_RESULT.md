# V13.2 Test Result

## Final commands

| Command | Result |
|---|---:|
| `.venv\Scripts\python.exe -m pytest backend/tests/test_v13_2_intelligent_journey_memory.py -q` | 3 passed |
| `.venv\Scripts\python.exe -m pytest backend/tests -q` | 380 passed, 2 skipped |
| `npm run build` in `frontend` | passed; Vite production bundle generated |
| Playwright CLI Chromium flow at `/v8/bookings` | passed; semantic draft + Memory + smart apply |

## Fresh-extract release gate

The final ZIP was extracted to a clean directory. Using the repository’s Python runtime outside the archive, the extracted backend passed the targeted V13.2/V13.1.2/V13.1.1/V13/V12/V10/V9 set: **41 passed**. The extracted frontend installed from `package-lock.json` and passed `npm run build`.

The first convergence regression exposed three concrete issues, all closed before the final run: OpenAPI did not list the three new routes; structured V13.1.2 imports were being pre-empted by the V13.2 semantic unresolved-field message; and a fresh artifact-first Journey did not initialize its trip context before Compose. The final run is green.

## Existing milestone coverage

The full backend run includes the V13.1.2 structural reservation tests, V13.1.1 semantic integrity tests, V13 integrity tests, V12 authoritative trip execution tests, V10 flagship tests, V9 real-trip operations tests, contract parity, and the rest of the repository backend suite.

## Runtime and evidence labels

- Backend: `LOCAL_TEST_RUNTIME`.
- DeepSeek contract witness: `SYNTHETIC_DEEPSEEK_FIXTURE`.
- Browser UI provider response: `UI_PROVIDER_REPLAY`.
- Authoritative planning facts in the Golden backend witness: `SYNTHETIC_FIXTURE` as explicitly labelled by the existing V12 evidence contract.

No live external provider or API-key-backed model result is represented as a passing live-provider claim in this report.
