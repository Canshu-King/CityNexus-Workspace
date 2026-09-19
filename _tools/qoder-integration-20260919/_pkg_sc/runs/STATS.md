# Numbers read back out of the files in this archive

So the figures quoted in INTEGRATION_REPORT.md sections 61-69 trace to artefacts
rather than to this document.  Nothing below was retyped by hand.

`runs/fe_full_convergence_authoritative.json` (run id scfull2, tree 79d2098)

```
{"expected": 46, "unexpected": 0, "flaky": 0, "skipped": 0, "duration_ms": 121149}
```

SQLite contention in the same stderr log: 0 occurrences of 'database is locked'.

Mutation check (`runs/mutation_check.log`): 7 sabotages killed, 1 survived.
The survivor is `F: an unresolvable C4 is skipped instead of failing closed`;
report section 67 records the measured reason (the feasibility gate intercepts
both reachable routes before that branch runs).

Concurrency schedules (`runs/concurrency_schedules.log`) print the final
canonical state each schedule produced, not just the HTTP statuses.
