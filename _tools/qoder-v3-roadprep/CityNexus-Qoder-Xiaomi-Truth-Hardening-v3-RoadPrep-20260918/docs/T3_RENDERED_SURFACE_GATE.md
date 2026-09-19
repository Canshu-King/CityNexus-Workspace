# T3 rendered surface gate

The Live rendered tests are useful and should remain.

Add a real `/v8/today` rendered case using the same fixture semantics.

Required matrix:

## ACK only
Today:
- unresolved change remains visible/countable.

Live:
- disruption visible;
- `已知晓，仍待处理` visible;
- handled state absent.

## Matching ACCEPTED replan
Today:
- no unresolved escalation for the trigger event.

Live:
- open/ack notices absent;
- handled state visible.

## Unrelated ACCEPTED replan
Both surfaces:
- trigger event remains unresolved.

Assertions must hit rendered DOM, not only imported helper functions.
