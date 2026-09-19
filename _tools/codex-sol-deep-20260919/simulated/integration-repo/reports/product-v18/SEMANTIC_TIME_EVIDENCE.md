# V18 Semantic Time Evidence

The server now treats semantic effective time and authoritative target facts
as separate decisions.

| Input state | Server result |
| --- | --- |
| Asserted FUTURE schedule disruption with a Journey end fact | Event is written with the Journey end timestamp and no invented Activity id |
| Asserted FUTURE closure with no unique Activity, Booking, Commitment, or Journey target | Review candidate only; `occurred_at` is null, no Event is persisted, recovery does not start |
| Unverified or hypothetical future claim | VERIFY_FACT / WHAT_IF path; no city Event |
| Asserted NOW disruption | Current execution position and current timestamp are used by the existing path |

Focused coverage includes future authoritative timing, ambiguous future review,
bounded evidence verification without Event creation, and preservation of the
existing V17 semantic envelope behavior. The database no longer records an
unresolved future claim as if it happened at the current time.
