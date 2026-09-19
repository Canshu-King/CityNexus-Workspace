# Race Condition Results

Final candidate: `776be4e`. Reference scope: one API process/worker using process-local Journey serialization.

| Schedule | Active plans | Accepted proposals | Dangling C4 | Result |
|---|---:|---:|---:|---|
| same proposal, same key | 1 | 1 | 0 | PASS |
| same proposal, different keys | 1 | 1 | 0 | PASS |
| competing proposals | 1 | 1 | 0 | PASS |
| booking CAPTURE vs accept plus concurrent read | 1 | 1 | 0 | PASS |
| restart and retry | 1 | 1 | 0 | PASS |

Machine evidence: `raw/final/concurrency_results.json`. Defect list: empty.

`PROCESS_LOCAL_ONLY` is deliberate and explicit. These results do not prove multi-worker safety. Production replacement: database row lock, advisory lock, or equivalent distributed serialization around the entire authoritative transaction.

The lock registry now uses `WeakValueDictionary`; the focused regression proves an unused Journey key is released after the critical section.
