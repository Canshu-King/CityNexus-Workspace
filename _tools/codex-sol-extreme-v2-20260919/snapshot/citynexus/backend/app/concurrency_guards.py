"""Process-local serialization for Journey-scoped authoritative writes.

The API currently runs SQLite in the reference/test deployment. SQLite does not
honour ``SELECT .. FOR UPDATE``, so two request sessions can both validate the
same active plan before either commits.  This guard keeps the complete
read/validate/write transaction atomic inside one API worker.  A distributed
deployment must replace or supplement it with a database/advisory lock.
"""

from __future__ import annotations

from contextlib import contextmanager
from threading import RLock
from typing import Iterator
from weakref import WeakValueDictionary


PROCESS_LOCAL_ONLY = True
_registry_guard = RLock()
_journey_locks: WeakValueDictionary[str, RLock] = WeakValueDictionary()


@contextmanager
def journey_write_lock(journey_id: str) -> Iterator[None]:
    """Serialize authoritative mutations for one Journey in this worker."""

    key = str(journey_id)
    with _registry_guard:
        lock = _journey_locks.get(key)
        if lock is None:
            lock = RLock()
            _journey_locks[key] = lock
    with lock:
        yield
