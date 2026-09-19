# Web-search evidence

`WebResearchProvider` uses DeepSeek server-side web search as perception only. A stored `WebObservation` includes URL, domain, title, capture time, source class, provider/model, excerpt, and SHA-256 evidence fingerprint, with `authority_status=NON_AUTHORITATIVE`.

The current live probe returned HTTP 200 but no source items. The implementation intentionally returns `NO_RESULTS` instead of inventing an `about:` URL for an unsourced summary. A model summary cannot authorize tool permissions, cancel a high-loss Commitment, or bypass the Autonomy Envelope.

Evidence tests cover:

- source-bearing observations retain URL and fingerprint;
- source-less summaries are not persisted as evidence;
- prompt-injection text remains untrusted data;
- the V10 flagship mocked provider stores an official-notice-shaped observation as non-authoritative.

External official-source capture remains `PARTIAL_EXTERNAL` until a configured DeepSeek response exposes a real source item or a sealed equivalent is replayed.

