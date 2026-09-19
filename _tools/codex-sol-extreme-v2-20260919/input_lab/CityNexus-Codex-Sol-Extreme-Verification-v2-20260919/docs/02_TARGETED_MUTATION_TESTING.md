# Track J — Targeted mutation adequacy audit

Goal:
Measure whether current truth/product gates would actually catch dangerous
regressions.

Do not brute-force every line. Mutate high-risk semantics only.

Seed mutations should include:
- ACK treated as resolved
- remove proposal->trigger_event linkage check
- unrelated ACCEPTED proposal closes all disruptions
- unknown/legacy provenance promoted to hard quality
- `hard_minutes` accepts None/unknown
- live provider failure falls back to mock as hard truth
- physical identity: None==None
- physical identity: coordinate-only SAME
- physical identity: cross-provider numeric token SAME
- replacement filtering admits AMBIGUOUS as safe SAME
- materiality check always true / always false
- protected commitment removed by replan
- partial budget evidence presented as full
- Live ignores `current_activity_id`
- stale cursor silently falls back to activity[0]

Implement mutants only in disposable clones.

For each mutant:
- exact symbol/file
- mutation diff
- focused gate set run
- KILLED or SURVIVED
- first killing test
- if SURVIVED, write the missing regression test

The goal is not a pretty mutation percentage. The goal is:
ZERO SURVIVORS for the listed catastrophic semantic mutants.

Deliver:
- mutation_manifest.json
- mutation_results.md
- survivor_regressions/
- raw/mutation_*.log
