"""Canonical Journey day/night semantics shared by planning and stay pricing."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class JourneyTemporalShape:
    """Calendar dates and overnight boundaries touched by a Journey."""

    day_count: int
    night_count: int


def derive_journey_temporal_shape(
    arrival_at: datetime,
    departure_at: datetime,
    *,
    min_day_count: int = 1,
    max_day_count: int = 7,
) -> JourneyTemporalShape:
    """Derive one calendar-date shape for every Journey consumer.

    A same-date Journey touches one calendar day and crosses no overnight
    boundary.  A departure on a later calendar date touches that many date
    boundaries plus the arrival date, so Oct 1 -> Oct 4 is 4 days / 3 nights.
    """

    if departure_at <= arrival_at:
        raise ValueError("V13_INVALID_ANCHOR_WINDOW")

    night_count = max(0, (departure_at.date() - arrival_at.date()).days)
    day_count = max(1, night_count + 1)
    if day_count < min_day_count or day_count > max_day_count:
        raise ValueError(f"V13_JOURNEY_DAYS_OUT_OF_BOUNDS:{day_count}")
    return JourneyTemporalShape(day_count=day_count, night_count=night_count)
