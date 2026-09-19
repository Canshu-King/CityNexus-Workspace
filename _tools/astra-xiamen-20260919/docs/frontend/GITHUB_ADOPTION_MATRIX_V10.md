# V10 UI adoption matrix

| Surface | Source/ref | Decision | License/authority note |
|---|---|---|---|
| Live route/evidence hierarchy | 21st.dev Codex/MCP, `Travel Route Card` id `7639` | Adapted independently for the Live Execution rail | No source was copied; 21st response did not expose a license grant, so the implementation is original |
| Server-state queries | TanStack Query 5 | Adopted for ExecutionClock/WebObservation reads | Dependency remains a frontend library; it cannot authorize actions |
| Icons | lucide-react | Adopted for status/evidence icons | Icons are presentation-only |
| QR/barcode | `@zxing/browser` | Adopted for deterministic Inbox decoding | Decoded values still require validation/confirmation |
| Accessibility | `@axe-core/playwright` | Adopted as an automated gate | Findings are machine-check evidence, not authority |

The 21st MCP endpoint and API key remain outside the repository. This ledger is the complete provenance record for V10 UI work.

