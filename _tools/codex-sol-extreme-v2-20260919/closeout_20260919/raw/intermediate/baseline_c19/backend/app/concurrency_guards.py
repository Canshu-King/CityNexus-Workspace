"""Process-local serialization for Journey-scoped authoritative writes.

The API currently runs SQLite in the reference/test deployment. SQLite does not
honour ``SELECT .. FOR UPDATE``, so two request sessions can both validate the
same active plan before either commits.  This guard keeps the complete
read/validate/write transaction atomic inside one API worker.  A distributed
deployment must replace or supplement it with a database/advisory lock.
"""

from __future__ import annotations

from collections import defaultdict
from contextlib import contextmanager
from threading import RLock
from typing import Iterator


_registry_guard = RLock()
_journey_locks: defaultdict[str, RLock] = defaultdict(RLock)


@contextmanager
def journey_write_lock(journey_id: str) -> Iterator[None]:
    """Serialize authoritative mutations for one Journey in this worker."""

    key = str(journey_id)
    with _registry_guard:
        lock = _journey_locks[key]
    with lock:
        yield
