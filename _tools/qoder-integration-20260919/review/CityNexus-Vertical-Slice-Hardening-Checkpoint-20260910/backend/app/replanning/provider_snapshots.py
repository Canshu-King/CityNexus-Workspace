from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Mapping


@dataclass(frozen=True)
class TravelEstimateFact:
    origin_key: str
    destination_key: str
    minutes: int
    provider_key: str
    captured_at: str
    degraded: bool = False

    def __post_init__(self) -> None:
        if self.minutes < 0:
            raise ValueError("travel minutes must be non-negative")


@dataclass(frozen=True)
class MobilitySnapshot:
    """Frozen travel facts consumed by the deterministic feasibility gate.

    External routing adapters run *before* the gate and their outputs are
    frozen into this value object.  The gate never performs a network call.
    """

    facts: Mapping[tuple[str, str], TravelEstimateFact]
    source_provider_key: str
    captured_at: str
    degraded: bool = False

    provider_key: str = "mobility-snapshot"
    is_frozen_snapshot: bool = True

    @classmethod
    def from_minutes(
        cls,
        *,
        source_provider_key: str,
        minutes: Mapping[tuple[str, str], int],
        captured_at: str | None = None,
        degraded: bool = False,
    ) -> MobilitySnapshot:
        stamp = captured_at or datetime.now(timezone.utc).isoformat()
        return cls(
            facts={
                pair: TravelEstimateFact(
                    origin_key=pair[0],
                    destination_key=pair[1],
                    minutes=int(value),
                    provider_key=source_provider_key,
                    captured_at=stamp,
                    degraded=degraded,
                )
                for pair, value in minutes.items()
            },
            source_provider_key=source_provider_key,
            captured_at=stamp,
            degraded=degraded,
        )

    def estimate_minutes(self, origin_key: str, destination_key: str) -> int:
        fact = self.facts.get((origin_key, destination_key))
        if fact is None:
            raise KeyError(f"missing frozen travel estimate: {origin_key}|{destination_key}")
        return fact.minutes
