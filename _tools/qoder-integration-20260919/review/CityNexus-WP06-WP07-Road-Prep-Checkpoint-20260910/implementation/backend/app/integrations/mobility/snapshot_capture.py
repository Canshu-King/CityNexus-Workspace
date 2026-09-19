from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Iterable, Protocol

from app.replanning.provider_snapshots import MobilitySnapshot, TravelEstimateFact


class MinuteEstimator(Protocol):
    provider_key: str

    def estimate_minutes(self, origin_key: str, destination_key: str) -> int: ...


class MobilitySnapshotCaptureError(RuntimeError):
    pass


@dataclass(frozen=True)
class MobilitySnapshotCaptureResult:
    snapshot: MobilitySnapshot
    failed_primary_pairs: tuple[tuple[str, str], ...]
    fallback_pairs: tuple[tuple[str, str], ...]

    @property
    def degraded(self) -> bool:
        return self.snapshot.degraded


def capture_mobility_snapshot(
    pairs: Iterable[tuple[str, str]],
    *,
    primary: MinuteEstimator,
    fallback: MinuteEstimator | None = None,
    captured_at: str | None = None,
) -> MobilitySnapshotCaptureResult:
    """Capture external mobility facts before the deterministic feasibility gate.

    The function deliberately performs provider calls outside the gate and freezes
    their results into ``MobilitySnapshot``. If the primary provider fails for a
    pair, an explicit fallback may fill that pair; the resulting snapshot is then
    marked degraded and every fact retains its own provider provenance.
    """

    stamp = captured_at or datetime.now(timezone.utc).isoformat()
    normalized_pairs = tuple(sorted({(str(a), str(b)) for a, b in pairs if a and b}))
    facts: dict[tuple[str, str], TravelEstimateFact] = {}
    primary_failures: list[tuple[str, str]] = []
    fallback_pairs: list[tuple[str, str]] = []

    for origin, destination in normalized_pairs:
        try:
            minutes = int(primary.estimate_minutes(origin, destination))
            if minutes < 0:
                raise ValueError("negative travel minutes")
            provider_key = str(primary.provider_key)
            degraded = False
        except Exception as primary_exc:  # external-provider boundary
            primary_failures.append((origin, destination))
            if fallback is None:
                raise MobilitySnapshotCaptureError(
                    f"mobility fact unavailable for {origin}|{destination}: "
                    f"{type(primary_exc).__name__}"
                ) from primary_exc
            try:
                minutes = int(fallback.estimate_minutes(origin, destination))
                if minutes < 0:
                    raise ValueError("negative fallback travel minutes")
            except Exception as fallback_exc:  # external-provider boundary
                raise MobilitySnapshotCaptureError(
                    f"primary and fallback mobility facts unavailable for {origin}|{destination}"
                ) from fallback_exc
            provider_key = str(fallback.provider_key)
            degraded = True
            fallback_pairs.append((origin, destination))

        facts[(origin, destination)] = TravelEstimateFact(
            origin_key=origin,
            destination_key=destination,
            minutes=minutes,
            provider_key=provider_key,
            captured_at=stamp,
            degraded=degraded,
        )

    snapshot = MobilitySnapshot(
        facts=facts,
        source_provider_key=str(primary.provider_key),
        captured_at=stamp,
        degraded=bool(primary_failures),
    )
    return MobilitySnapshotCaptureResult(
        snapshot=snapshot,
        failed_primary_pairs=tuple(primary_failures),
        fallback_pairs=tuple(fallback_pairs),
    )
