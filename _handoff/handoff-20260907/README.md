# CityNexus P1 Route Repair V3 - GPT Review Handoff

This package continues the external review of `CityNexus-P1-Route-Repair-V3-GPT-Opinion-20260907(2).zip`.

Files:

- `GPT-EXTERNAL-REVIEW.md`: independent review, reproduction notes, feasibility findings, and corrections to the current repair narrative.
- `CODEX-NEXT-INSTRUCTIONS.md`: concrete next-step instructions for Codex.
- `traveler-corridor-skeleton.yaml`: a validated **sub-solution only** for the 9 Traveler Association routes. It was checked together with the 3 frozen Extend routes and produced 0 geometry failures / 0 contacts within that subgraph. Do not treat it as a complete all-18 routing candidate.
- `EVIDENCE.json`: compact machine-readable review facts.

This handoff does not claim that the global 18-Association layout is solved. It gives Codex a clean subgraph, a corrected planning model, and strict acceptance criteria so the next iteration is less likely to produce another pile of geometrically legal-looking spaghetti.
