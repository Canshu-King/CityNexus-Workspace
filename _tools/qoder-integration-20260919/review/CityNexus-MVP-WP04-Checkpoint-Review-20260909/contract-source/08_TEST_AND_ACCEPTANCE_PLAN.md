# WP04 Test and Acceptance Plan

The CSV `tests/wp04_test_matrix.csv` is the executable checklist. Prioritise all P0 rows before broadening scope.

## Golden commerce scenario

1. Reset demo.
2. Generate >=2 feasible plans.
3. Select the canonical plan containing River Cruise at 15:30.
4. Query booking slot/provenance for `service-river-cruise-booking` (IR-006/FR-032).
5. Create booking for selected River Cruise Activity.
6. Verify provider CONFIRMED and ACTIVE commitment exists; canonical pre-payment strength is below C4.
7. CAPTURE payment with Idempotency-Key.
8. Verify transaction SUCCEEDED and external_ref exists.
9. Verify same semantic Commitment is strengthened using multi-factor policy.
10. Verify final strength rank 4 / exact source C4 code and stable semantic key/time.
11. Replay same payment key: same logical result, no provider call/transaction/strength duplicate.
12. Force booking failure: no false CONFIRMED commitment.
13. Force payment failure: FAILED transaction, no paid/anchored strengthening.
14. Open new DB session and retrieve commerce state unchanged.

## Gate before WP05

- all existing tests remain green;
- all P0 rows in WP04 matrix pass;
- canonical Golden commerce scenario passes offline;
- selected Journey feasibility invariant still passes after commerce writes;
- exact source five-level commitment enum is reconciled;
- no real network or payment secret introduced;
- requirement statuses updated conservatively.


## Order price-authority scenario

- use `service-food-preorder`;
- request SKU + quantity only (or deliberately forge a client price if backwards-compatible field remains);
- verify server catalog prices `local-lunch-box`/`jasmine-tea`;
- verify persisted total is computed server-side;
- then optionally CAPTURE an order payment to prove FR-036 target support.

Refund/void are not required for the WP04 Golden gate unless an unambiguous original-transaction reference is added. Do not mark FR-037 complete solely because enum labels exist.
