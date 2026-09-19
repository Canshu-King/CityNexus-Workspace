# CityNexus Product Experience + Stay & Mobility V8

## Outcome

V8 is implemented and locally verified as a stay-aware, multi-day, multimodal product experience while preserving the V7 entry point and regression surface. The flagship Tianjin request now creates a Journey with arrival/departure anchors, captured hotel evidence, Top-K stay + Journey options, explicit transport modes, editable Trip Studio state, a mobile Live Journey, a human-readable AI desk, and policy-gated autonomous weather recovery.

The delivery is a truthful captured/replay milestone. The reports explicitly separate local evidence from external integrations that were not configured.

## Product path

Natural-language intent is represented in the AI desk: keep the two-night stay around CNY 700, avoid long walks, prefer transit or taxi in rain, and handle the plan inside the user's authority envelope. CityNexus persists the multi-day context, captures four hotel offers, captures five mode facts, ranks complete stay + mobility options, and exposes the result in Journey Hub, Trip Studio, Stay Explorer, Live Journey, Bookings, Intelligence, Traveler Twin, AI desk, and the mobile Journey/Map/AI/Bookings/Me shell.

When RAIN is replayed, the server asks Delegation Policy whether a reversible transport change is allowed. With the tested AUTONOMOUS envelope, TRANSIT is executed, the option is regenerated, the provider-verified Event and audit decision are stored, and the deterministic post-action gate passes. With the default ADVISORY policy, the same route returns `REQUIRE_CONFIRMATION`. Durable commitments are preserved in both cases.

## Verification

- Backend final suite: `330 passed, 2 skipped, 2 warnings`; V8 focused + natural-language mission + contract tests passed and Ruff/compileall passed.
- Frontend final suite: `10 passed` in a serialized shared-SQLite run (V7/V6/V5/V4 legacy flows plus V8 desktop/mobile flows).
- Frontend build: Vite production build passed.
- OpenAPI runtime parity: passed after adding all V8 paths to `contracts/openapi.yaml`.
- Native DeepSeek: fresh process-only smoke `VALIDATED_AI`, deterministic gate `PASS`.
- Curated screenshots: `reports/product-v8/ui/before/` and `reports/product-v8/ui/after/`.
- V7 final archive remains untouched in the repository.
- Fresh-extract replay: the final archive extracted cleanly with all required files present; V8 + OpenAPI focused tests passed `8/8` from the extracted source.

## Explicit boundaries

Hermes model-backed execution, live hotel inventory, live transit routing, external Phoenix export, and model-backed Promptfoo are not claimed as completed. The checked-in adapters, provider statuses, local trace shape, and captured fallback path remain available for those integrations.

## Packaging

The final archive is `CityNexus-Product-Experience-Stay-Mobility-V8-Final-20260912.zip`. Staging excludes secrets, temporary DeepSeek environment files, virtual environments, node_modules, frontend dist output, databases, caches, browser reports, nested archives, and assist-package material.
