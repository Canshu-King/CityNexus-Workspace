#!/usr/bin/env python3
"""
CityNexus control-ledger write preflight.

Purpose:
- refuse CRLF / CR input;
- require one unique local anchor made from BEFORE + TARGET + AFTER;
- prove the proposed edit is local;
- prove the edit is byte-reversible before any write;
- optionally apply by atomic os.replace.

This is a control-plane guard, not a product-code utility.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import tempfile
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class EditReceipt:
    path: str
    original_sha256: str
    candidate_sha256: str
    original_size: int
    candidate_size: int
    lf_count_before: int
    lf_count_after: int
    anchor_hits: int
    edit_start: int
    edit_end: int
    replacement_size: int
    prefix_unchanged: bool
    suffix_unchanged: bool
    reversible: bool
    applied: bool


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def require_lf_only(data: bytes) -> None:
    if b"\r" in data:
        crlf = data.count(b"\r\n")
        lone_cr = data.count(b"\r") - crlf
        raise RuntimeError(
            f"NEWLINE_PROFILE_INVALID: CRLF={crlf}, lone_CR={lone_cr}; "
            "control ledger must be LF-only before editing"
        )


def count_occurrences(haystack: bytes, needle: bytes) -> int:
    if not needle:
        raise RuntimeError("EMPTY_ANCHOR_COMPONENT")
    count = 0
    start = 0
    while True:
        idx = haystack.find(needle, start)
        if idx < 0:
            return count
        count += 1
        start = idx + 1


def plan_edit(
    original: bytes,
    before: bytes,
    target: bytes,
    after: bytes,
    replacement: bytes,
) -> tuple[bytes, dict]:
    require_lf_only(original)

    anchor = before + target + after
    hits = count_occurrences(original, anchor)
    if hits != 1:
        raise RuntimeError(f"ANCHOR_NOT_UNIQUE: expected=1 observed={hits}")

    anchor_start = original.find(anchor)
    target_start = anchor_start + len(before)
    target_end = target_start + len(target)

    if original[target_start:target_end] != target:
        raise RuntimeError("TARGET_SPAN_MISMATCH")

    candidate = original[:target_start] + replacement + original[target_end:]
    require_lf_only(candidate)

    prefix_ok = candidate[:target_start] == original[:target_start]
    suffix_start_candidate = target_start + len(replacement)
    suffix_ok = candidate[suffix_start_candidate:] == original[target_end:]

    if not prefix_ok or not suffix_ok:
        raise RuntimeError(
            f"OUT_OF_SPAN_BYTE_DRIFT: prefix={prefix_ok} suffix={suffix_ok}"
        )

    # Reverse the exact planned span, not a global textual replace.
    reversed_bytes = (
        candidate[:target_start]
        + target
        + candidate[suffix_start_candidate:]
    )
    reversible = reversed_bytes == original
    if not reversible:
        raise RuntimeError("REVERSIBILITY_PROOF_FAILED")

    proof = {
        "anchor_hits": hits,
        "edit_start": target_start,
        "edit_end": target_end,
        "prefix_unchanged": prefix_ok,
        "suffix_unchanged": suffix_ok,
        "reversible": reversible,
    }
    return candidate, proof


def atomic_write(path: Path, candidate: bytes) -> None:
    parent = path.parent
    fd, tmp_name = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=parent)
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(candidate)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_name, path)
    finally:
        if os.path.exists(tmp_name):
            os.unlink(tmp_name)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("path", type=Path)
    p.add_argument("--before", required=True)
    p.add_argument("--target", required=True)
    p.add_argument("--after", required=True)
    p.add_argument("--replacement", required=True)
    p.add_argument(
        "--apply",
        action="store_true",
        help="Apply only after all preflight checks and reversible proof pass.",
    )
    return p.parse_args()


def main() -> int:
    args = parse_args()
    original = args.path.read_bytes()

    before = args.before.encode("utf-8")
    target = args.target.encode("utf-8")
    after = args.after.encode("utf-8")
    replacement = args.replacement.encode("utf-8")

    candidate, proof = plan_edit(
        original=original,
        before=before,
        target=target,
        after=after,
        replacement=replacement,
    )

    applied = False
    if args.apply:
        atomic_write(args.path, candidate)
        reread = args.path.read_bytes()
        if reread != candidate:
            raise RuntimeError("POST_WRITE_READBACK_MISMATCH")
        require_lf_only(reread)
        applied = True

    receipt = EditReceipt(
        path=str(args.path),
        original_sha256=sha256(original),
        candidate_sha256=sha256(candidate),
        original_size=len(original),
        candidate_size=len(candidate),
        lf_count_before=original.count(b"\n"),
        lf_count_after=candidate.count(b"\n"),
        anchor_hits=proof["anchor_hits"],
        edit_start=proof["edit_start"],
        edit_end=proof["edit_end"],
        replacement_size=len(replacement),
        prefix_unchanged=proof["prefix_unchanged"],
        suffix_unchanged=proof["suffix_unchanged"],
        reversible=proof["reversible"],
        applied=applied,
    )

    print(json.dumps(receipt.__dict__, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
