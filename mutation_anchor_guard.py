#!/usr/bin/env python3
"""Fail-closed helper for mutation drivers.

Use only on disposable / isolated worktrees.

It prevents two common false mutation verdicts:
1. anchor_hits == 0 but pytest still runs green;
2. replacement resolves to identical bytes, so no mutation actually happened.

The context manager always restores the original file bytes and verifies the
post-restore SHA-256 before returning.
"""

from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass, asdict
from hashlib import sha256
from pathlib import Path
from typing import Iterator
import json
import os
import tempfile


@dataclass(frozen=True)
class MutationReceipt:
    path: str
    anchor_hits: int
    expected_anchor_hits: int
    before_sha256: str
    mutated_sha256: str
    bytes_changed: bool


def _digest(data: bytes) -> str:
    return sha256(data).hexdigest()


def _atomic_write(path: Path, data: bytes) -> None:
    fd, tmp_name = tempfile.mkstemp(prefix=path.name + ".", dir=str(path.parent))
    try:
        with os.fdopen(fd, "wb") as fh:
            fh.write(data)
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp_name, path)
    except Exception:
        try:
            os.unlink(tmp_name)
        except FileNotFoundError:
            pass
        raise


@contextmanager
def temporary_guarded_replace(
    path: str | Path,
    before: bytes,
    after: bytes,
    *,
    expected_hits: int = 1,
) -> Iterator[MutationReceipt]:
    target = Path(path)
    original = target.read_bytes()
    original_sha = _digest(original)

    if before == after:
        raise RuntimeError("INVALID_MUTATION: before and after bytes are identical")

    hits = original.count(before)
    if hits != expected_hits:
        raise RuntimeError(
            f"HARNESS_INVALID: anchor_hits={hits}, expected={expected_hits}; mutation not applied"
        )

    mutated = original.replace(before, after, expected_hits)
    if mutated == original:
        raise RuntimeError("HARNESS_INVALID: mutation produced byte-identical file")

    mutated_sha = _digest(mutated)
    _atomic_write(target, mutated)

    reread = target.read_bytes()
    if reread != mutated:
        _atomic_write(target, original)
        raise RuntimeError("HARNESS_INVALID: mutated bytes did not persist exactly")

    receipt = MutationReceipt(
        path=str(target),
        anchor_hits=hits,
        expected_anchor_hits=expected_hits,
        before_sha256=original_sha,
        mutated_sha256=mutated_sha,
        bytes_changed=(original_sha != mutated_sha),
    )

    try:
        yield receipt
    finally:
        _atomic_write(target, original)
        restored = target.read_bytes()
        restored_sha = _digest(restored)
        if restored_sha != original_sha:
            raise RuntimeError(
                "RESTORE_FAILED: post-mutation file is not byte-identical to original"
            )


if __name__ == "__main__":
    print(json.dumps({
        "module": "mutation_anchor_guard",
        "usage": "import temporary_guarded_replace from this module",
        "required_invariants": [
            "anchor_hits == expected_hits",
            "mutated bytes != original bytes",
            "restore sha256 == original sha256",
        ],
    }, indent=2))
