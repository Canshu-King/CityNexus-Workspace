# Deep Track E — Cross-layer behavioral contract reconstruction

Goal:
Reconstruct CityNexus behavior end-to-end from backend truth -> API -> frontend
decision -> visible UI.

Build:
- `artifacts/contract_graph.json`
- `reports/CROSS_LAYER_CONTRACT_MAP.md`
- `reports/CROSS_LAYER_MISMATCHES.md`
- `reports/ENUM_AND_INTERNAL_LEAK_AUDIT.md`
- `tests/repro_*` for any concrete mismatch

Trace at minimum:
- Journey / active plan / selected plan
- Disruption lifecycle
- ACK vs resolution
- Replan proposal lifecycle
- trigger_event linkage
- mobility provenance / fact_quality
- booking / protected commitment survival
- budget evidence scope
- Today / Live / Trips visible state

Method:
- read source;
- use AST/static search where useful;
- run isolated read-only probes against disposable copies;
- record exact source file + symbol + API field + consumer.

Find:
- stale enum mappings;
- backend/frontend semantic drift;
- impossible UI states;
- raw internal labels escaping to consumer copy;
- states that backend can emit but frontend cannot distinguish;
- frontend assumptions not guaranteed by backend.

Do not merely list names. Produce concrete traces and minimal repros.
