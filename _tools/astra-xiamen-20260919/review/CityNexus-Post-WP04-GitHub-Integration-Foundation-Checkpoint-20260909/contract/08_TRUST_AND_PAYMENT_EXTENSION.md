# Trust and payment extension after WP04

WP04 remains mock payment first.

After the commerce domain is stable:
- keep `PaymentProvider` as the domain boundary;
- optional Stripe test adapter may be implemented from Stripe's samples;
- no Stripe-specific type enters the domain model;
- no production secret in repo/frontend;
- webhook/final-status handling must be idempotent.

## Step-up authentication

Use FastAPI-side `py_webauthn` when implementing Passkey/WebAuthn.

Step-up policy examples:
- ordinary Journey browsing: no step-up;
- initiating real/test payment: require recent step-up;
- refund/cancel paid booking: require step-up;
- sensitive transaction history: require step-up according to SRs.

WebAuthn is a Trust Layer, not the reason CityNexus exists.
