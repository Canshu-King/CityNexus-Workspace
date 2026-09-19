# Reuse notes for reference repositories

## PlacesRecommendation

Borrow the pipeline pattern:
`candidate generation -> real-world enrichment -> validation -> scoring -> explanation -> cache`.

Do not make its ASP.NET Core/.NET domain/database a permanent CityNexus runtime dependency. CityNexus already owns Place, Recommendation and AI provider boundaries.

## Travel-Story

Use as UI/provider abstraction reference. Do not fork and rename. CityNexus already has a different backend, domain, Journey lifecycle and coursework traceability model.

Useful underlying pieces are adopted directly instead: MapLibre and Turf.

## Stripe accept-a-payment

Reference implementation for a later test adapter only. Keep the current PaymentProvider contract and idempotency rules.

## Timefold

Keep for future comparative solver experiments; do not block the Python OR-Tools path.
