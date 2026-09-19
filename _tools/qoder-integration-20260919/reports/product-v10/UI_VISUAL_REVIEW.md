# V10 visual review

## Evidence files

Screenshots are under `reports/product-v10/ui-review/`, including:

- `journey-inbox-v10.png`
- `live-execution-v10-final.png`
- `live-execution-v10-mobile-viewport.png`
- earlier desktop/mobile/cycle screenshots retained for comparison.

## Review cycles

Cycle 1 used the Live Journey screenshot with DeepSeek vision as an advisory reviewer. High-confidence findings were:

- reduce the marketing-style hero dominance;
- remove duplicate NOW/NEXT noise;
- hide provider/WGS84/server-state jargon behind evidence disclosure;
- remove placeholder-like punctuation and raw execution labels;
- clarify the primary mobile action hierarchy.

Applied fixes include the compact Live heading, progressive Evidence drawer, traveler-facing copy, a visible Rain action, smaller execution rail, and mobile layout/contrast corrections. A new Inbox screenshot shows text/image extraction and deterministic QR scanning as separate, review-first surfaces.

Cycle 2 requested the strict JSON contract but external output failed parsing. It is recorded as `FAILED_EXTERNAL_PARSE`, not a visual PASS. Automated axe is authoritative for detectable accessibility and passed with zero violations; Playwright quality budget also passed.

