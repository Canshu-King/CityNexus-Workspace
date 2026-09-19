# V18.3 test results

## Focused gates

- V18.3 convergence tests + V18.2 productization + native client: 9 passed
- V18.1 native contract: passed
- V17 semantic, V16 integration, V15 Copilot, V14 recovery/reference gates:
  passed in the V18.2 baseline
- OpenAPI parity: passed

## Convergence gates

- Broad backend regression: 429 passed, 2 skipped, 2 warnings
- Frontend production build: passed; Vite emitted isolated maplibre-gl-* and
  JourneyMap-* chunks
- Playwright desktop native-Hermes flow: passed; real event rendering and
  CityNexus Stop proxy exercised at 1280x720 and 1440x900
- Playwright mobile flows: passed at 390x844 and 430x932 with compact mission
  sheet and expandable history; 320x720 overflow sanity also passed
- Package/fresh-extract gate: passed; required reports, code, and captures
  present; no databases, WAL/SHM, logs, caches, or secrets

## Truth caveat

Two bounded live DeepSeek Responses checks timed out. The product reports that
provider limitation honestly and never promotes a fallback or disconnected run
to native success. The qualifying native execution is documented in
HERMES_RUNTIME_EVIDENCE.md.
