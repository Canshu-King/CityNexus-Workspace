# V13.2 Golden Flow Evidence

## Backend witness

Test: `backend/tests/test_v13_2_intelligent_journey_memory.py::test_v132_golden_three_artifact_memory_to_authoritative_compose`

Result: passed.

The witness sends three artifacts through the text extraction endpoint using a deterministic DeepSeek-shaped test double:

1. inbound rail -> `ARRIVAL`, confidence `0.99`, structural target `arrival-anchor`;
2. paid Haihe cruise -> `MID_TRIP`, confidence `0.98`, target `place-river-cruise`;
3. return rail -> `DEPARTURE`, confidence `0.99`, structural target `departure-anchor`.

Each draft is evaluated by smart intake and applied through `smart-apply`. The Memory response is ordered as:

`ARRIVAL -> MID_TRIP -> DEPARTURE`

The final request enters `/plans/authoritative-compose` with the return reservation bound. Compose returns a candidate plan, and selecting it succeeds. This proves the semantic imports reach protected commitments and the existing authoritative planner rather than ending at an inbox-only record.

Runtime label: `LOCAL_TEST_RUNTIME` with `SYNTHETIC_DEEPSEEK_FIXTURE`; route facts remain deterministic and the hard feasibility gate remains authoritative.

## Review witness

Test: `test_v132_unknown_role_requires_review_then_user_patch_can_apply`

Result: passed.

An `UNKNOWN` semantic role is surfaced as `NEEDS_REVIEW`. The user patches the role to ARRIVAL through the draft PATCH endpoint, the server re-runs semantic intake and unresolved-field calculation, and smart apply then succeeds.

## Browser witness

Runtime: `LOCAL_CHROMIUM` through Playwright CLI at `/v8/bookings`.

Observed in the browser:

- Journey Memory rendered a three-item protected timeline with ARRIVAL, MID_TRIP, and DEPARTURE roles.
- The semantic draft rendered `MID_TRIP`, `98% confidence`, `Nexus River Cruise Pier`, `PAID`, and the model rationale.
- Scheduled departure/arrival fields and the anchor-role correction control rendered.
- `Apply smart decision` completed and the UI displayed `Semantic facts applied and protected in Journey Memory.`

Provider runtime label: `UI_PROVIDER_REPLAY`. The browser provider response was statically replayed in the browser session; no API key was persisted or included in the artifact.
