# DeepSeek Live Evidence Canary

## Configuration

The process environment contained neither `CITYNEXUS_AI_API_KEY` nor
`DEEPSEEK_API_KEY`. The live sanitized web-search probe was therefore recorded
as `NOT_CONFIGURED`; no key was copied from chat into the repository or a
checkpoint.

## Parser verification

The Responses normalizer was exercised with the provider-shaped envelope:

- `web_search_call.action.sources[]` URL/title/domain/snippet records;
- `message.content[].annotations[]` URL citations;
- duplicate URL/title observations are de-duplicated;
- a model summary without a source URL remains non-evidence.

The orchestration path persists returned observations as
`NON_AUTHORITATIVE` `WebObservation` rows. Opening hours and prices can only
be promoted by a completion that names captured observation IDs and passes the
existing official-source gate.
