# Next External Review Gate

Before the next GPT checkpoint, provide evidence for all of the following.

## Immediate repair gate

- previous checkpoint tests retained;
- new WP06 follow-up tests pass;
- `candidate_count=1` still finds a lower-ranked feasible candidate when the first raw candidate fails;
- Traveler preference changes alter verified `preference_fit` as expected;
- completed/past C4 no longer appears in `upcoming_commitments`;
- generation retry with supplied idempotency key does not create extra candidate PlanVersions;
- exact score ties no longer depend on random UUID ordering;
- opportunity value is neutral until real F3 evidence is wired.

## F3 gate

- F3 is either genuinely OpportunityWindow-backed or honestly renamed;
- next C4 travel + safety buffer are included exactly once;
- full candidate still passes authoritative feasibility.

## Provider gate

- Valhalla remains optional;
- live provider facts freeze into MobilitySnapshot before gate use;
- Open-Meteo creates only server-owned provider-verified evidence;
- provider recovery can resolve degradation state;
- no external service is required for default tests/demo.

## Advanced planning/AI gate

- OR-Tools, if enabled, only generates candidates;
- its output still passes the same gate;
- DeepSeek/LiteLLM receives verified evidence only;
- deterministic AI fallback remains functional.

## Packaging

Package files using exact repo-relative paths or include an explicit mapping. Include the dependency manifest and validation output. No hash manifests are required.
