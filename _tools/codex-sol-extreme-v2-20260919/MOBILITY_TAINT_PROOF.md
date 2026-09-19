# Mobility truth taint proof

Static flow is captured in `mobility_taint_graph.json`. The only hard-feasibility qualities are `EXPLICIT_FROZEN_FIXTURE` and `LIVE_PROVIDER_CAPTURE`.

Verified boundaries:

- capture records explicit provider quality; it does not infer trust from a provider name;
- deserialization promotes only an explicit quality or the exact historical `LIVE_CAPTURE` label;
- `CAPTURED_REPLAY`, synthetic, sealed-with-synthetic, mock and unknown/None do not become hard truth;
- `hard_minutes` enforces the two-value allowlist;
- a configured live hard capture has no mock fallback;
- a mixed snapshot cannot bless its weak member through a strong neighbor;
- accepted replans revalidate using persisted frozen evidence.

Dynamic evidence is in `tests/test_mobility_taint_extreme.py` and the focused regression log. The provenance-laundering, unknown-hard and mock-hard-fallback mutants were all killed.
