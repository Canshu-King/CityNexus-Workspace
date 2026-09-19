# V18.2 test results

## Focused gates

```text
V18.2 productization + native client + V18.1 native contract: 8 passed
V18.2 productization + V18.1 native + V17 semantic + V16 integration
  + V15 Copilot + V14 recovery/reference: 33 passed, 2 warnings
OpenAPI runtime/contract parity: 4 passed
```

## Convergence gates

```text
backend/tests (broad regression): 425 passed, 2 skipped, 2 warnings
frontend production build: passed (Vite/PWA; one large-chunk advisory)
```

The warnings are the existing Starlette/httpx and anyio deprecation notices;
the frontend advisory is the existing single large application chunk. No
failure was suppressed.

## Browser gates

Playwright exercised the sealed Tianjin demo and Copilot on desktop, then the
Copilot route at 390x844 and 430x932. The desktop flow showed
`HERMES_NATIVE_MCP`, real `inspect_journey`/`inspect_twin` events, and the Stop
proxy. The mobile flow showed the compact mission sheet and preserved the
ordered event history.

## Runtime caveat

The reused Windows User-scope DeepSeek credential was detected without printing
its value. Two direct Responses checks timed out; the app therefore rendered a
deterministic semantic fallback or an explicitly cancelled native run rather
than claiming unavailable Hermes work had completed. The qualifying native
execution is documented in `HERMES_AGENT_EVIDENCE.md`.
