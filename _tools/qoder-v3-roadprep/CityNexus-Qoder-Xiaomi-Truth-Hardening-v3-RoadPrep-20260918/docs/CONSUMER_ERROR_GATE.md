# Consumer error gate

Current `humanReplanReason()` returns raw input for an unmapped reason.

That can leak backend/internal text.

Required:

Known internal codes:
- mapped to traveler copy.

Unknown reason:
- generic safe copy, e.g.
  `暂时无法自动调整这段行程，请稍后重试或手动处理。`

Raw reason/code:
- Advanced / developer details only.

Regression:
an arbitrary backend string such as
`SQLITE_X_INTERNAL_FOO`
must not appear in default traveler DOM.
