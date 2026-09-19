# DeepSeek Contract and Diagnostics

DeepSeek remains the semantic layer. DiscoveryIntent receives Journey Memory, TravelerTwin preferences, protected commitments, anchor options, and weather context. Candidate curation receives the server candidate list and can return only those candidate IDs plus soft semantic fit and explanation.

The server retains deterministic ownership of coordinates, provider identity, opening hours, cost, route facts, feasibility, and committed state. Model output cannot create a Place ID, promote a price, or bypass the candidate gate.

The V13.4 focused diagnostic uses a mocked `402` response with provider code `insufficient_balance`. The resulting error exposes `status=402`, provider code, model, and safe response metadata only. The supplied DeepSeek key was not persisted or included in the archive.

Runtime label for the browser Golden was `SEALED_REPLAY_SEMANTIC_FALLBACK` because the isolated browser backend had AI disabled. The same route accepts the live DeepSeek client when configured; native sealed semantic fallback remains explicit and testable.
