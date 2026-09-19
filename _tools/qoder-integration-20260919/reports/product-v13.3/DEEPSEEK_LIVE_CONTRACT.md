# V13.3 DeepSeek Live Contract

## Contract implemented

- Text model default: `deepseek-v4-flash`.
- Dedicated vision model default: `deepseek-v4-flash-vision-exp`.
- Structured outputs use Responses API `text.format.type=json_schema`.
- Reservation interpretation includes semantic role, confidence, semantic target, and `candidate_journey_match`.
- DiscoveryIntent may select only a server-supplied symbolic anchor key and bounded query parameters.
- Candidate curation receives server IDs and returns soft semantic fit only; it cannot author coordinates, opening hours, cost, route, or commitments.

## Live probe

The supplied key was used only as `CITYNEXUS_AI_API_KEY` in a short-lived process. It was never written to a file, log, report, test fixture, or archive.

Result: `NOT_PROVEN`. The four text cases (`arrival_ticket`, `haihe_cruise`, `departure_ticket`, `unrelated_ticket`) each returned `DeepSeekResponsesError`. The optional vision case was skipped because no reservation image artifact was supplied for this run.

The sealed replay and deterministic fake-client contract remain the release proof. No live-provider success is claimed.

