# Rollback and reproduction plan

## Immutable references

- Main reference: `7d22cd0eb7840121ba42a5ba363e1a4c7ca1a7e7`.
- Integration baseline: `380e6ff`.
- Truth v6: `b12f24f`.
- Apple visual/IA: `e330ac2`.
- Type/behavior prerequisites: `a2124c0`.
- Real-seed/contrast: `cfb2b4a`.
- Current evidence snapshot: `1a8462dbc0108585266f637350202f9587ca532c`.

## Reproduce without touching protected trees

1. Clone the integration repository into a disposable directory outside all protected paths.
2. Checkout the exact full SHA in detached mode for verification, or create a local verification branch there.
3. Set AI keys empty and use a temporary database path. Never reuse production data.
4. Run focused truth/provider gates, then backend full regression only once if the focused hypothesis passes.
5. Run frontend typecheck/build/qoder gates/full seeded E2E with isolated ports and storage state.
6. Record commands, tool versions, exit codes and output hashes.

## Rollback layers

| Fault introduced by | Roll back disposable/release branch to | Verification |
| --- | --- | --- |
| Evidence/capture commit | `cfb2b4a` | Tests unchanged; screenshots/tooling removed |
| Seed/contrast changes | `a2124c0` | Original qoder gates, build/typecheck |
| Type/behavior group B | `e330ac2` | Visual gates plus explicit type errors expected from old line |
| Visual/IA group A | `b12f24f` | Truth tests and baseline frontend behavior |
| Truth v6 | `380e6ff` | Baseline 762/15/0; do not ship because truth fixes are lost |

Rollback means moving only an owner-created disposable/release reference to an already-recorded commit. Never reset or clean the three protected working trees. Database/test data rollback uses a disposable DB deletion/recreation, never a production Journey reset.
