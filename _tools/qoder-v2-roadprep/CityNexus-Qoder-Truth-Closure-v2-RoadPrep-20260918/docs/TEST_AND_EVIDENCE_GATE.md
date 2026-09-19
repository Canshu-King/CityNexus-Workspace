# Test and Evidence Gate

The next package must stop calling browser-imported pure-module checks "E2E".

Use these labels:

- unit
- component/integration
- API/service integration
- visible browser E2E

## Required deliverables

- raw focused test output
- raw authoritative relevant-suite output
- baseline vs patched failure lists
- exact source baseline identifier
- changed files
- clean patch
- no unsupported statement that a test covers behavior it does not execute

## Minimum test layers

### T1
Unit + replacement-family integration.

### T2
Unit + actual `/replans` API/service integration.

### T3
Unit + rendered Today/Live integration.

### T4
Unit + rendered budget UI integration.

## Full suite

A baseline-vs-patch failure-set comparison is useful, but the package must
include enough raw logs to independently inspect the failures.

Do not classify an existing failure as "environment only" without preserving
its traceback/assertion in the handoff.
